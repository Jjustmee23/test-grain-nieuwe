from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
import openpyxl
import pandas as pd
import logging
from datetime import datetime
from decimal import Decimal
import os
from difflib import SequenceMatcher

from mill.models import Batch, Factory, City, BatchTemplate
from mill.services.batch_production_service import BatchProductionService

logger = logging.getLogger(__name__)

def is_super_admin(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_super_admin)
def batch_import_view(request):
    """
    Main view for batch Excel import
    """
    if request.method == 'POST':
        return handle_batch_import(request)
    
    # Get available factories and cities for context
    factories = Factory.objects.filter(status=True).order_by('name')
    cities = City.objects.filter(status=True).order_by('name')
    batch_templates = BatchTemplate.objects.filter(is_active=True).order_by('name')
    
    context = {
        'factories': factories,
        'cities': cities,
        'batch_templates': batch_templates,
    }
    
    return render(request, 'batches/batch_import.html', context)

def handle_batch_import(request):
    """
    Handle the batch import from Excel files
    """
    logger.info("=== BATCH IMPORT STARTED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request FILES: {list(request.FILES.keys())}")
    logger.info(f"Request POST: {list(request.POST.keys())}")
    
    try:
        excel_files = request.FILES.getlist('excel_files')
        import_type = request.POST.get('import_type', 'auto')
        city_id = request.POST.get('city_id')
        factory_id = request.POST.get('factory_id')
        batch_template_id = request.POST.get('batch_template_id')
        start_date = request.POST.get('start_date')
        
        logger.info(f"Excel files count: {len(excel_files)}")
        logger.info(f"Import type: {import_type}")
        logger.info(f"City ID: {city_id}")
        logger.info(f"Factory ID: {factory_id}")
        
        if not excel_files:
            logger.error("No Excel files provided")
            messages.error(request, _('Please select at least one Excel file.'))
            return redirect('batch-import')
        
        # Process files and collect results
        all_results = []
        total_matched = 0
        total_unmatched = 0
        total_batches_created = 0
        total_batches_updated = 0
        
        for excel_file in excel_files:
            logger.info(f"Processing file: {excel_file.name}")
            
            # Read and validate Excel file
            df = pd.read_excel(excel_file)
            df = validate_excel_data(df)
            
            # Get factories for matching
            factories = Factory.objects.filter(status=True)
            
            # Separate matched and unmatched rows
            matched_rows = []
            unmatched_rows = []
            
            for idx, row in df.iterrows():
                mill_name = row['mill_name']
                net_grains = row['net_grains']
                
                # Try to find factory match
                factory = get_factory_for_import(mill_name, import_type, city_id, factory_id)
                
                if factory:
                    matched_rows.append({
                        'row_data': row,
                        'factory': factory,
                        'mill_name': mill_name,
                        'net_grains': net_grains
                    })
                    total_matched += 1
                else:
                    suggestions = _get_factory_suggestions(mill_name, factories)
                    unmatched_rows.append({
                        'row_data': row,
                        'mill_name': mill_name,
                        'net_grains': net_grains,
                        'suggestions': suggestions
                    })
                    total_unmatched += 1
            
            # Process matched rows
            logger.info(f"Processing {len(matched_rows)} matched rows...")
            for item in matched_rows:
                try:
                    batch_result = process_batch_row(
                        item['row_data'], import_type, city_id, factory_id, 
                        batch_template_id, start_date
                    )
                    
                    if batch_result['created']:
                        total_batches_created += 1
                        logger.info(f"✅ Batch created for {item['mill_name']}")
                    elif batch_result['updated']:
                        total_batches_updated += 1
                        logger.info(f"🔄 Batch updated for {item['mill_name']}")
                        
                except Exception as e:
                    logger.error(f"Error processing matched row: {str(e)}")
            
            # Store results
            all_results.append({
                'filename': excel_file.name,
                'matched_rows': matched_rows,
                'unmatched_rows': unmatched_rows,
                'batches_created': len([r for r in matched_rows if r.get('processed', False)]),
                'batches_updated': 0
            })
        
        # Show results
        success_message = _('Import completed successfully!')
        success_message += f'\n✅ Matched mills processed: {total_matched}'
        success_message += f'\n📦 Batches created: {total_batches_created}'
        success_message += f'\n🔄 Batches updated: {total_batches_updated}'
        
        if total_unmatched > 0:
            # Store unmatched data in session for manual processing
            request.session['unmatched_batches'] = _serialize_unmatched_data(all_results)
            
            success_message += f'\n\n❌ Unmatched mills: {total_unmatched}'
            success_message += f'\n📋 You can now process the {total_unmatched} unmatched mills manually.'
            
            messages.success(request, success_message)
            return redirect('batch-manual-process')
        else:
            messages.success(request, success_message)
            return redirect('batch-list')
        
    except Exception as e:
        logger.error(f"Batch import error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        messages.error(request, f'Import failed: {str(e)}')
        return redirect('batch-import')

def process_excel_file(excel_file, import_type, city_id, factory_id, batch_template_id, start_date):
    """
    Process a single Excel file for batch import
    """
    logger.info(f"=== PROCESSING FILE: {excel_file.name} ===")
    
    result = {
        'filename': excel_file.name,
        'batches_created': 0,
        'batches_updated': 0,
        'errors': [],
        'matches_found': 0,
        'matches_not_found': 0
    }
    
    try:
        # Read Excel file
        logger.info("Reading Excel file...")
        df = pd.read_excel(excel_file)
        logger.info(f"Excel file read: {df.shape}")
        
        # Validate and clean data
        logger.info("Validating data...")
        df = validate_excel_data(df)
        logger.info(f"Data validated: {df.shape}")
        
        # Process each row
        logger.info("Starting to process rows...")
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    logger.info(f"Processing row {index + 1}: {row['mill_name']}")
                    batch_result = process_batch_row(
                        row, import_type, city_id, factory_id, 
                        batch_template_id, start_date
                    )
                    
                    if batch_result['created']:
                        result['batches_created'] += 1
                        logger.info(f"✅ Batch created for {row['mill_name']}")
                    elif batch_result['updated']:
                        result['batches_updated'] += 1
                        logger.info(f"🔄 Batch updated for {row['mill_name']}")
                    
                    if batch_result['factory_found']:
                        result['matches_found'] += 1
                    else:
                        result['matches_not_found'] += 1
                        logger.warning(f"❌ No factory found for {row['mill_name']}")
                    
                    if batch_result['error']:
                        result['errors'].append(f"Row {index + 2}: {batch_result['error']}")
                        logger.error(f"Error in row {index + 2}: {batch_result['error']}")
                        
                except Exception as e:
                    result['errors'].append(f"Row {index + 2}: {str(e)}")
                    logger.error(f"Error processing row {index + 2}: {str(e)}")
        
        logger.info(f"File processing completed: {result['batches_created']} created, {result['batches_updated']} updated")
        
    except Exception as e:
        result['errors'].append(f"File processing error: {str(e)}")
        logger.error(f"Excel file processing error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    return result

def validate_excel_data(df):
    """
    Validate and clean Excel data - Enhanced for different document formats
    """
    logger.info(f"=== VALIDATING EXCEL DATA ===")
    logger.info(f"Original DataFrame shape: {df.shape}")
    logger.info(f"Original columns: {list(df.columns)}")
    
    # First, try to detect if this is a Nineveh-style document (many columns)
    if len(df.columns) > 20:
        logger.info("Detected Nineveh-style document with many columns")
        return _process_nineveh_document(df)
    
    # Try to find Arabic headers in the data
    df = _find_and_restructure_headers(df)
    
    # Try to map columns to expected format
    df = _map_columns_to_standard(df)
    
    # Validate required columns
    required_columns = ['mill_name', 'capacity', 'net_grains']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        logger.error(f"Available columns: {list(df.columns)}")
        logger.error(f"DataFrame shape: {df.shape}")
        
        # Show first few rows for debugging
        logger.error("First 3 rows of data:")
        for idx, row in df.head(3).iterrows():
            logger.error(f"Row {idx}: {dict(row)}")
        
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Clean data
    df = df.dropna(subset=['mill_name'])  # Remove rows without mill name
    df['capacity'] = pd.to_numeric(df['capacity'], errors='coerce').fillna(0)
    df['net_grains'] = pd.to_numeric(df['net_grains'], errors='coerce').fillna(0)
    
    logger.info(f"Final DataFrame shape: {df.shape}")
    logger.info(f"Final columns: {list(df.columns)}")
    
    return df

def _process_nineveh_document(df):
    """Process Nineveh-style documents with specific column structure"""
    logger.info("Processing Nineveh-style document...")
    
    data_rows = []
    for idx, row in df.iterrows():
        try:
            # Extract data from specific columns
            mill_name = row.iloc[18] if len(row) > 18 else None  # Column 18 (mill name)
            capacity = row.iloc[16] if len(row) > 16 else None   # Column 16 (capacity)
            net_grains = row.iloc[12] if len(row) > 12 else None # Column 12 (net grains)
            serial = row.iloc[21] if len(row) > 21 else None     # Column 21 (serial number)
            
            # Validate mill name
            if pd.notna(mill_name) and str(mill_name).strip() and str(mill_name) != 'اسم المطحنة':
                # Validate numeric data
                if pd.notna(capacity) and pd.notna(net_grains):
                    try:
                        capacity_val = float(capacity)
                        net_grains_val = float(net_grains)
                        
                        data_rows.append({
                            'mill_name': str(mill_name).strip(),
                            'capacity': capacity_val,
                            'net_grains': net_grains_val,
                            'serial_number': serial if pd.notna(serial) else idx + 1
                        })
                        logger.info(f"Added row {idx}: {mill_name} - {net_grains_val} tons")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Skipping row {idx}: invalid numeric data - {e}")
        except Exception as e:
            logger.warning(f"Error processing row {idx}: {e}")
    
    if not data_rows:
        raise ValueError("No valid data rows found in Nineveh-style document")
    
    # Create new DataFrame from extracted data
    df = pd.DataFrame(data_rows)
    logger.info(f"Created DataFrame from Nineveh data: {df.shape}")
    return df

def _find_and_restructure_headers(df):
    """Find Arabic headers and restructure DataFrame"""
    logger.info("Looking for Arabic headers...")
    
    # If we have unnamed columns, try to identify the data structure
    if any('Unnamed' in str(col) for col in df.columns):
        logger.info("Detected unnamed columns, searching for Arabic headers...")
        
        # Look for the first row that contains Arabic text (likely headers)
        for idx, row in df.iterrows():
            row_values = [str(val) for val in row.values if pd.notna(val)]
            arabic_text = [val for val in row_values if any('\u0600' <= char <= '\u06FF' for char in val)]
            
            if len(arabic_text) >= 2:  # At least 2 Arabic columns
                logger.info(f"Found Arabic headers at row {idx}: {arabic_text}")
                
                # Create new DataFrame starting from this row
                df = df.iloc[idx:].reset_index(drop=True)
                df.columns = df.iloc[0]
                df = df.iloc[1:].reset_index(drop=True)
                logger.info(f"Restructured DataFrame columns: {list(df.columns)}")
                break
    
    return df

def _map_columns_to_standard(df):
    """Map column names to standard format"""
    logger.info("Mapping columns to standard format...")
    
    # Expected columns mapping (Arabic and English)
    expected_columns = {
        # Arabic columns from documents
        'اسم المطحنة': 'mill_name',
        'الطاقة التصميمية': 'capacity',
        'صافي الحبوب': 'net_grains',
        'ت': 'serial_number',
        
        # English columns (alternative names)
        'mill_name': 'mill_name',
        'capacity': 'capacity',
        'net_grains': 'net_grains',
        'serial_number': 'serial_number',
        
        # Optional columns
        'التاريخ': 'date',
        'date': 'date',
        'batch_number': 'batch_number',
        'رقم الحصة': 'batch_number'
    }
    
    # Rename columns to standard names
    df = df.rename(columns=expected_columns)
    logger.info(f"Columns after mapping: {list(df.columns)}")
    
    return df

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_factory_match(mill_name, factories):
    """Find the best matching factory for a mill name"""
    best_match = None
    best_score = 0
    
    for factory in factories:
        # Exact match
        if factory.name == mill_name:
            return factory, 1.0
        
        # Calculate similarity
        score = similarity(factory.name, mill_name)
        if score > best_score:
            best_score = score
            best_match = factory
    
    return best_match, best_score

def process_batch_row(row, import_type, city_id, factory_id, batch_template_id, start_date):
    """
    Process a single row from Excel and create/update batch
    """
    result = {
        'created': False, 
        'updated': False, 
        'error': None,
        'factory_found': False
    }
    
    try:
        mill_name = str(row['mill_name']).strip()
        capacity = Decimal(str(row['capacity']))
        net_grains = Decimal(str(row.get('net_grains', 0)))
        
        # Get factory based on import type
        factory = get_factory_for_import(mill_name, import_type, city_id, factory_id)
        
        if not factory:
            result['error'] = f"Factory not found for mill: {mill_name}"
            return result
        
        result['factory_found'] = True
        
        # Get or create batch number
        batch_number = get_batch_number(row, factory)
        
        # Check if batch already exists
        existing_batch = Batch.objects.filter(
            batch_number=batch_number,
            factory=factory
        ).first()
        
        if existing_batch:
            # Update existing batch
            existing_batch.wheat_amount = net_grains
            existing_batch.expected_flour_output = calculate_expected_output(net_grains, batch_template_id)
            existing_batch.save()
            result['updated'] = True
        else:
            # Create new batch
            batch_data = {
                'batch_number': batch_number,
                'factory': factory,
                'wheat_amount': net_grains,
                'expected_flour_output': calculate_expected_output(net_grains, batch_template_id),
                'status': 'pending',
                'is_completed': False,
            }
            
            # Add start date if provided
            if start_date:
                try:
                    batch_data['start_date'] = datetime.strptime(start_date, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            # Add template data if provided
            if batch_template_id:
                template = BatchTemplate.objects.get(id=batch_template_id)
                batch_data['waste_factor'] = template.waste_factor
            
            Batch.objects.create(**batch_data)
            result['created'] = True
            
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Error processing batch row: {str(e)}")
    
    return result

def get_factory_for_import(mill_name, import_type, city_id, factory_id):
    """
    Get factory based on import type and parameters - Enhanced with smart matching
    """
    if import_type == 'single':
        # Single factory import
        return Factory.objects.get(id=factory_id)
    
    elif import_type == 'city':
        # City import - find factory by name in the city
        city_factories = Factory.objects.filter(
            city_id=city_id,
            status=True
        )
        best_match, score = find_best_factory_match(mill_name, city_factories)
        return best_match if score > 0.5 else None
    
    else:
        # Auto-detect factory by name - Enhanced matching
        all_factories = Factory.objects.filter(status=True)
        
        # First try to find in Mosul factories (for Nineveh documents)
        mosul_factories = all_factories.filter(city__name__icontains='موصل')
        best_match, score = find_best_factory_match(mill_name, mosul_factories)
        
        if best_match and score > 0.5:
            return best_match
        
        # If no good match in Mosul, try all factories
        best_match, score = find_best_factory_match(mill_name, all_factories)
        return best_match if score > 0.5 else None

def get_batch_number(row, factory):
    """
    Generate or extract batch number
    """
    # Try to get batch number from Excel
    if 'batch_number' in row and pd.notna(row['batch_number']):
        return str(row['batch_number'])
    
    # Generate batch number based on factory and date
    current_date = timezone.now().date()
    existing_batches = Batch.objects.filter(
        factory=factory,
        created_at__date=current_date
    ).count()
    
    return f"{factory.name}_{current_date.strftime('%Y%m%d')}_{existing_batches + 1:03d}"

def calculate_expected_output(wheat_amount, batch_template_id):
    """
    Calculate expected flour output based on template or default values
    """
    if batch_template_id:
        try:
            template = BatchTemplate.objects.get(id=batch_template_id)
            waste_factor = template.waste_factor
        except BatchTemplate.DoesNotExist:
            waste_factor = Decimal('20.0')  # Default 20% waste
    else:
        waste_factor = Decimal('20.0')  # Default 20% waste
    
    return wheat_amount * ((100 - waste_factor) / 100)

@login_required
@user_passes_test(is_super_admin)
def batch_import_preview(request):
    """
    Preview Excel data before import
    """
    logger.info("Preview function called")
    
    if request.method == 'POST':
        logger.info("POST request received")
        
        if request.FILES.get('excel_file'):
            excel_file = request.FILES['excel_file']
            logger.info(f"Excel file received: {excel_file.name}")
            
            try:
                # Read Excel file with different header options
                logger.info("Reading Excel file...")
                
                # Try reading with different header rows
                for header_row in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
                    try:
                        df = pd.read_excel(excel_file, header=header_row)
                        logger.info(f"Excel file read with header row {header_row}. Shape: {df.shape}")
                        logger.info(f"Columns: {list(df.columns)}")
                        
                        # Check if we have meaningful column names (not all Unnamed)
                        unnamed_cols = [col for col in df.columns if 'Unnamed' in str(col)]
                        if len(unnamed_cols) < len(df.columns) * 0.5:  # Less than 50% unnamed
                            break
                    except Exception as e:
                        logger.warning(f"Failed to read with header row {header_row}: {str(e)}")
                        continue
                else:
                    # If all header rows failed, try without header
                    df = pd.read_excel(excel_file, header=None)
                    logger.info(f"Excel file read without header. Shape: {df.shape}")
                
                logger.info(f"Final columns: {list(df.columns)}")
                
                # Validate and clean data
                logger.info("Validating data...")
                df = validate_excel_data(df)
                logger.info(f"Data validated. Shape after validation: {df.shape}")
                
                # Store the validated data in session for later use
                request.session['preview_excel_data'] = {
                    'filename': excel_file.name,
                    'data': df.to_dict('records'),
                    'shape': df.shape
                }
                
                # Get preview data (first 10 rows for display)
                preview_data = df.head(10).to_dict('records')
                logger.info(f"Preview data created. Rows: {len(preview_data)}")
                
                # Get available factories for matching
                factories = Factory.objects.filter(status=True).order_by('name')
                logger.info(f"Factories loaded: {factories.count()}")
                
                # Add factory matching info to preview data (first 10 rows for display)
                for item in preview_data:
                    mill_name = item['mill_name']
                    best_match, score = find_best_factory_match(mill_name, factories)
                    
                    if best_match and score > 0.5:
                        item['factory_match'] = best_match.name
                        item['match_score'] = f"{score:.2f}"
                    else:
                        item['factory_match'] = 'No match'
                        item['match_score'] = '0.00'
                
                # Calculate full matching statistics for ALL rows
                total_matches = 0
                total_unmatched = 0
                total_grains = 0
                
                for idx, row in df.iterrows():
                    mill_name = row['mill_name']
                    net_grains = row['net_grains']
                    best_match, score = find_best_factory_match(mill_name, factories)
                    
                    if best_match and score > 0.5:
                        total_matches += 1
                        total_grains += net_grains
                    else:
                        total_unmatched += 1
                
                context = {
                    'preview_data': preview_data,
                    'factories': factories,
                    'filename': excel_file.name,
                    'total_rows': len(df),
                    'total_matches': total_matches,
                    'total_unmatched': total_unmatched,
                    'total_grains': total_grains,
                    'match_percentage': (total_matches / len(df) * 100) if len(df) > 0 else 0
                }
                
                return render(request, 'batches/batch_import_preview.html', context)
                
            except Exception as e:
                logger.error(f"Error in preview: {str(e)}")
                messages.error(request, f'Error reading Excel file: {str(e)}')
                return redirect('batch-import')
        else:
            messages.error(request, _('Please select an Excel file.'))
            return redirect('batch-import')
    
    return redirect('batch-import')

@login_required
@user_passes_test(is_super_admin)
def download_batch_template(request):
    """
    Download Excel template for batch import
    """
    try:
        import xlsxwriter
        from io import BytesIO
        
        # Create Excel file in memory
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Batch Import Template')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D7E4BC',
            'border': 1,
            'align': 'center'
        })
        
        data_format = workbook.add_format({
            'border': 1
        })
        
        # Headers (Arabic) - Document style
        headers = [
            'ت',
            'اسم المطحنة',
            'الطاقة التصميمية',
            'صافي الحبوب'
        ]
        
        # Write headers
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Set column widths - Arabic document style
        column_widths = [8, 25, 20, 20]
        for col, width in enumerate(column_widths):
            worksheet.set_column(col, col, width)
        
        # Add sample data - Arabic document style
        sample_data = [
            [1, 'دينوي', 400, 2059],
            [2, 'محسن الدوري الفيصل', 300, 1544],
            [3, 'الموصل', 250, 1287],
            [4, 'سنجار', 200, 1029],
            [5, 'البعاج', 150, 772],
        ]
        
        for row, data in enumerate(sample_data, start=1):
            for col, value in enumerate(data):
                worksheet.write(row, col, value, data_format)
        
        workbook.close()
        output.seek(0)
        
        # Create response
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="batch_import_template.xlsx"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        messages.error(request, f'Error creating template: {str(e)}')
        return redirect('batch-import') 

def process_matched_batches_only(request):
    """
    Process only matched batches and return unmatched for manual processing
    """
    logger.info("=== PROCESSING MATCHED BATCHES ONLY ===")
    
    try:
        excel_files = request.FILES.getlist('excel_files')
        import_type = request.POST.get('import_type', 'auto')
        city_id = request.POST.get('city_id')
        factory_id = request.POST.get('factory_id')
        batch_template_id = request.POST.get('batch_template_id')
        start_date = request.POST.get('start_date')
        
        logger.info(f"Excel files count: {len(excel_files)}")
        
        if not excel_files:
            messages.error(request, _('Please select at least one Excel file.'))
            return redirect('batch-import')
        
        # Process files and collect results
        all_results = []
        total_matched = 0
        total_unmatched = 0
        total_batches_created = 0
        total_batches_updated = 0
        
        for excel_file in excel_files:
            logger.info(f"Processing file: {excel_file.name}")
            
            # Read and validate Excel file
            df = pd.read_excel(excel_file)
            df = validate_excel_data(df)
            
            # Get factories for matching
            factories = Factory.objects.filter(status=True)
            
            # Separate matched and unmatched rows
            matched_rows = []
            unmatched_rows = []
            
            for idx, row in df.iterrows():
                mill_name = row['mill_name']
                net_grains = row['net_grains']
                
                # Try to find factory match
                factory = get_factory_for_import(mill_name, import_type, city_id, factory_id)
                
                if factory:
                    matched_rows.append({
                        'row_data': row,
                        'factory': factory,
                        'mill_name': mill_name,
                        'net_grains': net_grains
                    })
                    total_matched += 1
                else:
                    unmatched_rows.append({
                        'row_data': row,
                        'mill_name': mill_name,
                        'net_grains': net_grains,
                        'suggestions': _get_factory_suggestions(mill_name, factories)
                    })
                    total_unmatched += 1
            
            # Process matched rows
            logger.info(f"Processing {len(matched_rows)} matched rows...")
            for item in matched_rows:
                try:
                    batch_result = process_batch_row(
                        item['row_data'], import_type, city_id, factory_id, 
                        batch_template_id, start_date
                    )
                    
                    if batch_result['created']:
                        total_batches_created += 1
                    elif batch_result['updated']:
                        total_batches_updated += 1
                        
                except Exception as e:
                    logger.error(f"Error processing matched row: {str(e)}")
            
            # Store results
            all_results.append({
                'filename': excel_file.name,
                'matched_rows': matched_rows,
                'unmatched_rows': unmatched_rows,
                'batches_created': len([r for r in matched_rows if r.get('processed', False)]),
                'batches_updated': 0
            })
        
        # Store unmatched data in session for manual processing
        request.session['unmatched_batches'] = _serialize_unmatched_data(all_results)
        
        # Show results
        success_message = _('Import completed successfully!')
        success_message += f'\n✅ Matched mills processed: {total_matched}'
        success_message += f'\n❌ Unmatched mills: {total_unmatched}'
        success_message += f'\n📦 Batches created: {total_batches_created}'
        success_message += f'\n🔄 Batches updated: {total_batches_updated}'
        
        if total_unmatched > 0:
            success_message += f'\n\n📋 You can now process the {total_unmatched} unmatched mills manually.'
        
        messages.success(request, success_message)
        
        # Redirect to manual processing if there are unmatched
        if total_unmatched > 0:
            return redirect('batch-manual-process')
        else:
            return redirect('batch-list')
            
    except Exception as e:
        logger.error(f"Error in matched-only processing: {str(e)}")
        messages.error(request, f'Import failed: {str(e)}')
        return redirect('batch-import')

def _get_factory_suggestions(mill_name, factories, max_suggestions=5):
    """Get factory name suggestions for unmatched mills"""
    suggestions = []
    
    for factory in factories:
        score = similarity(mill_name, factory.name)
        if score > 0.3:  # Lower threshold for suggestions
            suggestions.append({
                'factory': factory,
                'score': score,
                'name': factory.name,
                'city': factory.city.name
            })
    
    # Sort by score and return top suggestions
    suggestions.sort(key=lambda x: x['score'], reverse=True)
    return suggestions[:max_suggestions]

def _serialize_unmatched_data(all_results):
    """Serialize unmatched data for session storage"""
    serialized = []
    
    for result in all_results:
        file_data = {
            'filename': result['filename'],
            'unmatched_rows': []
        }
        
        for item in result['unmatched_rows']:
            row_data = {
                'mill_name': item['mill_name'],
                'net_grains': float(item['net_grains']),
                'capacity': float(item['row_data']['capacity']),
                'serial_number': item['row_data'].get('serial_number', ''),
                'suggestions': [
                    {
                        'factory_id': s['factory'].id,
                        'factory_name': s['factory'].name,
                        'city_name': s['city'],
                        'score': s['score']
                    }
                    for s in item['suggestions']
                ]
            }
            file_data['unmatched_rows'].append(row_data)
        
        serialized.append(file_data)
    
    return serialized

@login_required
@user_passes_test(is_super_admin)
def process_preview_data(request):
    """
    Process the data that was previewed
    """
    logger.info("=== PROCESSING PREVIEW DATA ===")
    
    try:
        # Get preview data from session
        preview_data = request.session.get('preview_excel_data')
        
        if not preview_data:
            messages.error(request, _('No preview data found. Please upload the file again.'))
            return redirect('batch-import')
        
        # Get form data
        import_type = request.POST.get('import_type', 'auto')
        city_id = request.POST.get('city_id')
        factory_id = request.POST.get('factory_id')
        batch_template_id = request.POST.get('batch_template_id')
        start_date = request.POST.get('start_date')
        
        logger.info(f"Processing preview data: {preview_data['shape']}")
        logger.info(f"Import type: {import_type}")
        
        # Convert session data back to DataFrame
        df_data = preview_data['data']
        
        # Get factories for matching
        factories = Factory.objects.filter(status=True)
        
        # Separate matched and unmatched rows
        matched_rows = []
        unmatched_rows = []
        total_matched = 0
        total_unmatched = 0
        total_batches_created = 0
        total_batches_updated = 0
        
        for row_data in df_data:
            mill_name = row_data['mill_name']
            net_grains = row_data['net_grains']
            
            # Try to find factory match
            factory = get_factory_for_import(mill_name, import_type, city_id, factory_id)
            
            if factory:
                matched_rows.append({
                    'row_data': row_data,
                    'factory': factory,
                    'mill_name': mill_name,
                    'net_grains': net_grains
                })
                total_matched += 1
            else:
                suggestions = _get_factory_suggestions(mill_name, factories)
                unmatched_rows.append({
                    'row_data': row_data,
                    'mill_name': mill_name,
                    'net_grains': net_grains,
                    'suggestions': suggestions
                })
                total_unmatched += 1
        
        # Process matched rows
        logger.info(f"Processing {len(matched_rows)} matched rows...")
        for item in matched_rows:
            try:
                batch_result = process_batch_row(
                    item['row_data'], import_type, city_id, factory_id, 
                    batch_template_id, start_date
                )
                
                if batch_result['created']:
                    total_batches_created += 1
                    logger.info(f"✅ Batch created for {item['mill_name']}")
                elif batch_result['updated']:
                    total_batches_updated += 1
                    logger.info(f"🔄 Batch updated for {item['mill_name']}")
                    
            except Exception as e:
                logger.error(f"Error processing matched row: {str(e)}")
        
        # Store results for manual processing if needed
        all_results = [{
            'filename': preview_data['filename'],
            'matched_rows': matched_rows,
            'unmatched_rows': unmatched_rows,
            'batches_created': total_batches_created,
            'batches_updated': total_batches_updated
        }]
        
        # Show results
        success_message = _('Import completed successfully!')
        success_message += f'\n✅ Matched mills processed: {total_matched}'
        success_message += f'\n📦 Batches created: {total_batches_created}'
        success_message += f'\n🔄 Batches updated: {total_batches_updated}'
        
        if total_unmatched > 0:
            # Store unmatched data in session for manual processing
            request.session['unmatched_batches'] = _serialize_unmatched_data(all_results)
            
            success_message += f'\n\n❌ Unmatched mills: {total_unmatched}'
            success_message += f'\n📋 You can now process the {total_unmatched} unmatched mills manually.'
            
            messages.success(request, success_message)
            return redirect('batch-manual-process')
        else:
            messages.success(request, success_message)
            return redirect('batch-list')
        
        # Clear preview data from session
        if 'preview_excel_data' in request.session:
            del request.session['preview_excel_data']
        
    except Exception as e:
        logger.error(f"Error processing preview data: {str(e)}")
        messages.error(request, f'Import failed: {str(e)}')
        return redirect('batch-import')

@login_required
@user_passes_test(is_super_admin)
def batch_manual_process(request):
    """
    Manual processing of unmatched batches
    """
    logger.info("=== MANUAL BATCH PROCESSING ===")
    
    # Get unmatched data from session
    unmatched_data = request.session.get('unmatched_batches', [])
    
    if not unmatched_data:
        messages.warning(request, _('No unmatched batches to process.'))
        return redirect('batch-import')
    
    if request.method == 'POST':
        # Process manual assignments
        processed_count = 0
        errors = []
        
        for file_data in unmatched_data:
            for row_data in file_data['unmatched_rows']:
                mill_name = row_data['mill_name']
                factory_id = request.POST.get(f'factory_{mill_name}')
                net_grains = request.POST.get(f'grains_{mill_name}')
                
                if factory_id and net_grains:
                    try:
                        factory = Factory.objects.get(id=factory_id)
                        net_grains_val = float(net_grains)
                        
                        # Create batch manually
                        batch_result = _create_batch_manually(
                            factory, net_grains_val, row_data
                        )
                        
                        if batch_result['success']:
                            processed_count += 1
                        else:
                            errors.append(f"{mill_name}: {batch_result['error']}")
                            
                    except Exception as e:
                        errors.append(f"{mill_name}: {str(e)}")
        
        # Clear session data
        del request.session['unmatched_batches']
        
        # Show results
        if processed_count > 0:
            messages.success(request, f'Successfully processed {processed_count} unmatched batches.')
        
        if errors:
            error_message = f'Errors occurred: {len(errors)} batches failed.'
            for error in errors[:5]:  # Show first 5 errors
                error_message += f'\n- {error}'
            messages.error(request, error_message)
        
        return redirect('batch-list')
    
    # Get all factories for dropdown
    factories = Factory.objects.filter(status=True).order_by('name')
    
    context = {
        'unmatched_data': unmatched_data,
        'factories': factories,
        'total_unmatched': sum(len(file_data['unmatched_rows']) for file_data in unmatched_data)
    }
    
    return render(request, 'batches/batch_manual_process.html', context)

def _create_batch_manually(factory, net_grains, row_data):
    """Create a batch manually for unmatched mill"""
    try:
        # Generate batch number
        current_date = timezone.now().date()
        existing_batches = Batch.objects.filter(
            factory=factory,
            created_at__date=current_date
        ).count()
        
        batch_number = f"{factory.name}_{current_date.strftime('%Y%m%d')}_{existing_batches + 1:03d}"
        
        # Create batch
        batch = Batch.objects.create(
            batch_number=batch_number,
            factory=factory,
            wheat_amount=net_grains,
            expected_flour_output=net_grains * 0.8,  # 80% efficiency
            status='pending',
            start_date=current_date
        )
        
        return {
            'success': True,
            'batch': batch
        }
        
    except Exception as e:
        logger.error(f"Error creating manual batch: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        } 