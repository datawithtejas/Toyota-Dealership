from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras

app = Flask(__name__)
CORS(app)  # Allows HTML to talk to this server

# --- CONFIGURATION ---
DB_CONFIG = {
    "dbname": "Warehouse toyota",     
    "user": "postgres",             
    "password": "Data@0410",    
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# --- API ENDPOINTS ---

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Vehicle")
    vehicles = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Shipment")
    shipments = cur.fetchone()[0]
    conn.close()
    return jsonify({"vehicles": vehicles, "shipments": shipments})

@app.route('/api/chart-data', methods=['GET'])
def get_chart_data():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = """
        WITH MonthlyShipmentCounts AS (
            SELECT DealerID, TO_CHAR(ShipDate, 'YYYY-MM') AS ShipmentMonth, COUNT(ShipmentID) AS TotalShipments 
            FROM Shipment GROUP BY DealerID, TO_CHAR(ShipDate, 'YYYY-MM')
        )
        SELECT D.Name as dealership, MSC.ShipmentMonth, MSC.TotalShipments 
        FROM MonthlyShipmentCounts MSC
        JOIN Dealership D ON MSC.DealerID = D.DealerID
        ORDER BY MSC.ShipmentMonth DESC LIMIT 10;
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/update-status', methods=['POST'])
def update_status():
    data = request.json
    vin = data['vin']
    status = data['status']
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE ShipmentVehicle SET VehicleStatus = %s WHERE VIN = %s", (status, vin))
        conn.commit()
        msg = "Status Updated!"
        if status == 'Received':
            msg += " (Trigger Fired)"
    except Exception as e:
        conn.rollback()
        msg = str(e)
    finally:
        conn.close()
    
    return jsonify({"message": msg})

@app.route('/api/audit-logs', methods=['GET'])
def get_logs():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM ShipmentStatus ORDER BY Timestamp DESC LIMIT 20")
    data = cur.fetchall()
    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)