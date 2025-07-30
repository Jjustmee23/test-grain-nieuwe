#!/usr/bin/env python3
"""
🛡️ VOLLEDIGE BACKUP SCRIPT - UC300 Reset Pilot
Maak een complete backup van alle data en code voordat we de pilot starten
"""

import os
import sys
import subprocess
import datetime
import shutil
import psycopg2
from pathlib import Path

class FullSystemBackup:
    
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
    
    def backup_database(self, db_config, db_name):
        """Backup a PostgreSQL database"""
        try:
            self.log(f"🔄 Starting backup of database: {db_name}")
            
            backup_file = f"{self.backup_dir}/databases/{db_name}_{self.backup_time}.sql"
            
            # Use pg_dump to create SQL backup
            cmd = [
                'pg_dump',
                f"--host={db_config['host']}",
                f"--port={db_config['port']}", 
                f"--username={db_config['user']}",
                f"--dbname={db_config['database']}",
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                f"--file={backup_file}"
            ]
            
            # Set password via environment
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Verify backup file exists and has content
                if os.path.exists(backup_file) and os.path.getsize(backup_file) > 1000:
                    self.log(f"✅ Database {db_name} backup successful: {backup_file}")
                    self.log(f"   Backup size: {os.path.getsize(backup_file)} bytes")
                    return True
                else:
                    self.log(f"❌ Database {db_name} backup file is empty or missing")
                    return False
            else:
                self.log(f"❌ Database {db_name} backup failed:")
                self.log(f"   STDOUT: {result.stdout}")
                self.log(f"   STDERR: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ ERROR backing up database {db_name}: {str(e)}")
            return False
    
    def backup_specific_tables(self, db_config, db_name, tables):
        """Backup specific tables with data"""
        try:
            for table in tables:
                self.log(f"🔄 Backing up table: {table} from {db_name}")
                
                backup_file = f"{self.backup_dir}/databases/{db_name}_{table}_{self.backup_time}.sql"
                
                cmd = [
                    'pg_dump',
                    f"--host={db_config['host']}",
                    f"--port={db_config['port']}", 
                    f"--username={db_config['user']}",
                    f"--dbname={db_config['database']}",
                    f"--table={table}",
                    '--data-only',
                    '--inserts',
                    f"--file={backup_file}"
                ]
                
                env = os.environ.copy()
                env['PGPASSWORD'] = db_config['password']
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log(f"✅ Table {table} backup successful")
                else:
                    self.log(f"❌ Table {table} backup failed: {result.stderr}")
                    
        except Exception as e:
            self.log(f"❌ ERROR backing up tables: {str(e)}")
    
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
    
    def create_restore_script(self):
        """Create a restore script for easy rollback"""
        try:
            restore_script = f"{self.backup_dir}/restore_backup.sh"
            
            script_content = f'''#!/bin/bash
# 🔄 RESTORE SCRIPT - UC300 Pilot Rollback
# Created: {datetime.datetime.now()}

echo "🛡️ STARTING SYSTEM RESTORE FROM BACKUP"
echo "Backup directory: {self.backup_dir}"
echo "⚠️  WARNING: This will restore the system to the state before UC300 pilot!"
echo ""

read -p "Are you sure you want to continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 1
fi

echo "🔄 Restoring databases..."

# Restore counter database
echo "Restoring counter database..."
export PGPASSWORD="{self.db1_config['password']}"
psql -h {self.db1_config['host']} -p {self.db1_config['port']} -U {self.db1_config['user']} -d {self.db1_config['database']} < {self.backup_dir}/databases/counter_{self.backup_time}.sql

# Restore testdb database  
echo "Restoring testdb database..."
export PGPASSWORD="{self.db2_config['password']}"
psql -h {self.db2_config['host']} -p {self.db2_config['port']} -U {self.db2_config['user']} -d {self.db2_config['database']} < {self.backup_dir}/databases/testdb_{self.backup_time}.sql

echo "🔄 Restoring code..."
# Restore code (ask for confirmation before overwriting)
read -p "Restore code files? This will overwrite current code! (yes/no): " restore_code
if [ "$restore_code" = "yes" ]; then
    rm -rf /home/administrator/mill-mqtt_backup_temp
    mv /home/administrator/mill-mqtt /home/administrator/mill-mqtt_backup_temp
    cp -r {self.backup_dir}/code/mill-mqtt /home/administrator/
    
    rm -rf /home/administrator/project-mill-application_backup_temp  
    mv /home/administrator/project-mill-application /home/administrator/project-mill-application_backup_temp
    cp -r {self.backup_dir}/code/project-mill-application /home/administrator/
    
    echo "✅ Code restored. Previous code backed up with _backup_temp suffix"
fi

echo "✅ RESTORE COMPLETED!"
echo "Please restart services and verify system functionality."
'''
            
            with open(restore_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Make script executable
            os.chmod(restore_script, 0o755)
            
            self.log(f"✅ Restore script created: {restore_script}")
            return True
            
        except Exception as e:
            self.log(f"❌ ERROR creating restore script: {str(e)}")
            return False
    
    def run_full_backup(self):
        """Execute complete backup process"""
        self.log("🛡️ STARTING FULL SYSTEM BACKUP FOR UC300 PILOT")
        self.log("=" * 60)
        
        # Create backup directory
        if not self.create_backup_directory():
            return False
        
        backup_success = True
        
        # Backup databases
        self.log("\n📊 BACKING UP DATABASES")
        self.log("-" * 30)
        
        if not self.backup_database(self.db1_config, "counter"):
            backup_success = False
        
        if not self.backup_database(self.db2_config, "testdb"):
            backup_success = False
        
        # Backup critical tables separately for extra safety
        self.log("\n📋 BACKING UP CRITICAL TABLES")
        self.log("-" * 30)
        
        critical_tables = ['mqtt_data', 'raw_mqtt_data']
        self.backup_specific_tables(self.db1_config, "counter", critical_tables)
        
        critical_tables_app = ['mill_productiondata', 'mill_device']
        self.backup_specific_tables(self.db2_config, "testdb", critical_tables_app)
        
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
        
        # Create restore script
        self.log("\n🔄 CREATING RESTORE SCRIPT")
        self.log("-" * 30)
        
        if not self.create_restore_script():
            backup_success = False
        
        # Final summary
        self.log("\n" + "=" * 60)
        if backup_success:
            self.log("✅ FULL BACKUP COMPLETED SUCCESSFULLY!")
            self.log(f"📁 Backup location: {self.backup_dir}")
            self.log(f"🔄 Restore script: {self.backup_dir}/restore_backup.sh")
            self.log("\n🛡️ YOUR SYSTEM IS NOW SAFELY BACKED UP!")
            self.log("Ready to proceed with UC300 pilot implementation.")
        else:
            self.log("❌ BACKUP COMPLETED WITH ERRORS!")
            self.log("Please review the log and fix any issues before proceeding.")
        
        return backup_success

def main():
    """Run the full system backup"""
    print("🛡️ UC300 PILOT - FULL SYSTEM BACKUP")
    print("=" * 50)
    print()
    
    backup = FullSystemBackup()
    success = backup.run_full_backup()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Backup completed successfully ✅")
        print("2. Ready for UC300 pilot implementation ✅") 
        print("3. Rollback available if needed ✅")
        print("\nYou can now safely proceed with the pilot!")
    else:
        print("\n⚠️ BACKUP ISSUES DETECTED")
        print("Please resolve any errors before proceeding with pilot.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 