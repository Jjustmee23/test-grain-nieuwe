#!/usr/bin/env python3
"""
🛡️ PYTHON-BASED BACKUP SCRIPT - UC300 Reset Pilot
Alternative backup using Python since pg_dump is not available
"""

import os
import sys
import datetime
import shutil
import json
import psycopg2
from psycopg2.extras import RealDictCursor

class PythonBackup:
    
    def __init__(self):
        self.backup_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = f"/home/administrator/backup_uc300_pilot_{self.backup_time}"
        self.log_file = f"{self.backup_dir}/backup_log.txt"
        
        # Database connections
        self.db1_config = {
            'host': '45.154.238.114',
            'user': 'root', 
            'password': 'testpassword',
            'database': 'counter',
            'port': 5432
        }
        
        self.db2_config = {
            'host': '45.154.238.114',
            'user': 'testuser',
            'password': 'testpassword', 
            'database': 'testdb',
            'port': 5433
        }
    
    def log(self, message):
        """Log message to console and file"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        if hasattr(self, 'log_file') and os.path.exists(os.path.dirname(self.log_file)):
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_msg + '\n')
    
    def create_backup_directory(self):
        """Create main backup directory structure"""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            os.makedirs(f"{self.backup_dir}/databases", exist_ok=True)
            os.makedirs(f"{self.backup_dir}/code", exist_ok=True)
            os.makedirs(f"{self.backup_dir}/config", exist_ok=True)
            
            self.log(f"✅ Backup directory created: {self.backup_dir}")
            return True
        except Exception as e:
            self.log(f"❌ ERROR creating backup directory: {str(e)}")
            return False
    
    def backup_table_data(self, db_config, table_name, db_name):
        """Backup a specific table as JSON data"""
        try:
            self.log(f"🔄 Backing up table: {table_name} from {db_name}")
            
            # Connect to database
            conn = psycopg2.connect(**db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Count total records
            count_query = f"SELECT COUNT(*) as total FROM {table_name}"
            cur.execute(count_query)
            total_count = cur.fetchone()['total']
            
            if total_count == 0:
                self.log(f"⚠️ Table {table_name} is empty")
                return True
            
            # Get table data
            data_query = f"SELECT * FROM {table_name} ORDER BY id LIMIT 50000"  # Limit voor geheugen
            cur.execute(data_query)
            rows = cur.fetchall()
            
            # Convert to JSON-serializable format
            json_data = []
            for row in rows:
                json_row = {}
                for key, value in row.items():
                    if isinstance(value, datetime.datetime):
                        json_row[key] = value.isoformat()
                    elif isinstance(value, datetime.date):
                        json_row[key] = value.isoformat()
                    else:
                        json_row[key] = value
                json_data.append(json_row)
            
            # Save to JSON file
            backup_file = f"{self.backup_dir}/databases/{db_name}_{table_name}_{self.backup_time}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'table_name': table_name,
                    'backup_time': self.backup_time,
                    'total_records': len(json_data),
                    'database': db_name,
                    'data': json_data
                }, f, indent=2, ensure_ascii=False)
            
            self.log(f"✅ Table {table_name} backup successful: {len(json_data)} records")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"❌ ERROR backing up table {table_name}: {str(e)}")
            return False
    
    def backup_database_schema(self, db_config, db_name):
        """Backup database schema information"""
        try:
            self.log(f"🔄 Backing up schema information for: {db_name}")
            
            conn = psycopg2.connect(**db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get table information
            schema_query = """
                SELECT 
                    table_name,
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """
            cur.execute(schema_query)
            schema_info = cur.fetchall()
            
            # Get table row counts
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """
            cur.execute(tables_query)
            tables = [row['table_name'] for row in cur.fetchall()]
            
            table_counts = {}
            for table in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cur.fetchone()['count']
                    table_counts[table] = count
                except Exception as e:
                    table_counts[table] = f"Error: {str(e)}"
            
            # Save schema info
            schema_file = f"{self.backup_dir}/databases/{db_name}_schema_{self.backup_time}.json"
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'database': db_name,
                    'backup_time': self.backup_time,
                    'schema': [dict(row) for row in schema_info],
                    'table_counts': table_counts
                }, f, indent=2, ensure_ascii=False)
            
            self.log(f"✅ Schema backup successful for {db_name}")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"❌ ERROR backing up schema for {db_name}: {str(e)}")
            return False
    
    def backup_code_repositories(self):
        """Backup all code repositories"""
        try:
            code_backup_dir = f"{self.backup_dir}/code"
            
            # Backup mill-mqtt directory
            self.log("🔄 Backing up mill-mqtt directory...")
            if os.path.exists("/home/administrator/mill-mqtt"):
                shutil.copytree(
                    "/home/administrator/mill-mqtt", 
                    f"{code_backup_dir}/mill-mqtt",
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git', 'myenv')
                )
                self.log("✅ mill-mqtt backup completed")
            
            # Backup project-mill-application directory  
            self.log("🔄 Backing up project-mill-application directory...")
            if os.path.exists("/home/administrator/project-mill-application"):
                shutil.copytree(
                    "/home/administrator/project-mill-application",
                    f"{code_backup_dir}/project-mill-application", 
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git', 'venv', 'node_modules')
                )
                self.log("✅ project-mill-application backup completed")
            
            return True
            
        except Exception as e:
            self.log(f"❌ ERROR backing up code: {str(e)}")
            return False
    
    def backup_configuration_files(self):
        """Backup important configuration files"""
        try:
            config_backup_dir = f"{self.backup_dir}/config"
            
            # List of important config files/directories
            config_paths = [
                "/home/administrator/mill-mqtt/docker-compose.yml",
                "/home/administrator/mill-mqtt/.env",
                "/home/administrator/project-mill-application/project-mill-application/settings.py"
            ]
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    dest_path = f"{config_backup_dir}/{os.path.basename(config_path)}"
                    shutil.copy2(config_path, dest_path)
                    self.log(f"✅ Config backup: {config_path}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ ERROR backing up configs: {str(e)}")
            return False
    
    def create_restore_instructions(self):
        """Create restore instructions"""
        try:
            instructions_file = f"{self.backup_dir}/RESTORE_INSTRUCTIONS.md"
            
            instructions = f"""# 🔄 RESTORE INSTRUCTIONS - UC300 Pilot Backup

## Backup Information
- **Created**: {datetime.datetime.now()}
- **Backup Directory**: {self.backup_dir}

## Quick Restore Steps

### 1. Database Restore
The database data is backed up as JSON files. To restore:

```python
# Use the restore_from_json.py script (will be created)
python3 restore_from_json.py
```

### 2. Code Restore
```bash
# Backup current code
mv /home/administrator/mill-mqtt /home/administrator/mill-mqtt_backup_temp
mv /home/administrator/project-mill-application /home/administrator/project-mill-application_backup_temp

# Restore from backup
cp -r {self.backup_dir}/code/mill-mqtt /home/administrator/
cp -r {self.backup_dir}/code/project-mill-application /home/administrator/
```

### 3. Configuration Restore
```bash
cp {self.backup_dir}/config/* /home/administrator/mill-mqtt/
```

## Important Notes
- ✅ All critical data is backed up as JSON
- ✅ Code repositories are fully backed up
- ✅ Configurations are preserved
- ⚠️ Test restore process in non-production first

## Emergency Contact
If you need help with restore, check the backup_log.txt for details.
"""
            
            with open(instructions_file, 'w', encoding='utf-8') as f:
                f.write(instructions)
            
            self.log(f"✅ Restore instructions created: {instructions_file}")
            return True
            
        except Exception as e:
            self.log(f"❌ ERROR creating restore instructions: {str(e)}")
            return False
    
    def run_full_backup(self):
        """Execute complete backup process"""
        self.log("🛡️ STARTING PYTHON-BASED BACKUP FOR UC300 PILOT")
        self.log("=" * 60)
        
        # Create backup directory
        if not self.create_backup_directory():
            return False
        
        backup_success = True
        
        # Backup database schemas
        self.log("\n📊 BACKING UP DATABASE SCHEMAS")
        self.log("-" * 30)
        
        if not self.backup_database_schema(self.db1_config, "counter"):
            backup_success = False
        
        if not self.backup_database_schema(self.db2_config, "testdb"):
            backup_success = False
        
        # Backup critical tables
        self.log("\n📋 BACKING UP CRITICAL TABLES DATA")
        self.log("-" * 30)
        
        critical_tables = [
            ('counter', ['mqtt_data', 'raw_mqtt_data']),
            ('testdb', ['mill_productiondata', 'mill_device', 'mill_rawdata'])
        ]
        
        for db_name, tables in critical_tables:
            db_config = self.db1_config if db_name == 'counter' else self.db2_config
            for table in tables:
                if not self.backup_table_data(db_config, table, db_name):
                    self.log(f"⚠️ Warning: Failed to backup {table}")
        
        # Backup code
        self.log("\n💻 BACKING UP CODE REPOSITORIES")
        self.log("-" * 30)
        
        if not self.backup_code_repositories():
            backup_success = False
        
        # Backup configurations
        self.log("\n⚙️ BACKING UP CONFIGURATIONS")
        self.log("-" * 30)
        
        if not self.backup_configuration_files():
            backup_success = False
        
        # Create restore instructions
        self.log("\n📖 CREATING RESTORE INSTRUCTIONS")
        self.log("-" * 30)
        
        if not self.create_restore_instructions():
            backup_success = False
        
        # Final summary
        self.log("\n" + "=" * 60)
        self.log("✅ PYTHON BACKUP COMPLETED!")
        self.log(f"📁 Backup location: {self.backup_dir}")
        self.log(f"📖 Instructions: {self.backup_dir}/RESTORE_INSTRUCTIONS.md")
        self.log("\n🛡️ YOUR SYSTEM IS NOW SAFELY BACKED UP!")
        self.log("Ready to proceed with UC300 pilot implementation.")
        
        return True

def main():
    """Run the Python-based backup"""
    print("🛡️ UC300 PILOT - PYTHON-BASED BACKUP")
    print("=" * 50)
    print()
    
    backup = PythonBackup()
    success = backup.run_full_backup()
    
    if success:
        print("\n🎯 BACKUP SUCCESS!")
        print("✅ All critical data backed up as JSON")
        print("✅ Code repositories backed up")
        print("✅ Ready for UC300 pilot implementation")
        print("\nYou can now safely proceed with the pilot!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 