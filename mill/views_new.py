

import psycopg2
from django.shortcuts import render
from django.http import HttpResponse

def testmill(request):
    # PostgreSQL connection settings (replace with actual credentials)
    db_settings = {
        "dbname": "counter",
        "user": "root",
        "password": "testpassword",
        "host": "45.154.238.114",
        "port": "5432",  # Default is 5432
    }

    try:
        # Connect to PostgreSQL manually
        conn = psycopg2.connect(**db_settings)
        cursor = conn.cursor()

        # Run a raw SQL query
        # Query 1: Latest Data for Each counter_id
        cursor.execute("""
            WITH RankedData AS (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (PARTITION BY counter_id ORDER BY timestamp DESC) AS rn
                FROM 
                    mqtt_data
            )
            SELECT 
                *
            FROM 
                RankedData
            WHERE 
                rn = 1
            ORDER BY 
                timestamp DESC;
        """)
        data = cursor.fetchall()  # Fetch all rows

        # Query 2: Latest Data for Each counter_id from Yesterday
        cursor.execute("""
            WITH RankedData AS (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (PARTITION BY counter_id ORDER BY timestamp DESC) AS rn
                FROM 
                    mqtt_data
                WHERE 
                    timestamp::date = CURRENT_DATE - INTERVAL '1 day'  -- Filter for yesterday's date
            )
            SELECT 
                *
            FROM 
                RankedData
            WHERE 
                rn = 1
            ORDER BY 
                timestamp DESC;
        """)
        yesterday_data = cursor.fetchall()  # Fetch all rows

        # Close the cursor and connection
        cursor.close()
        conn.close()
 

    # print(data)
    except Exception as e:
        return HttpResponse(f"Database Error: {str(e)}")

    # Pass data to the template
    return render(request, "mill/testmill.html", {"data": data, "yesterday":yesterday_data})

