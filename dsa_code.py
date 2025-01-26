import tkinter as tk
from tkinter import messagebox
import mysql.connector

# Database setup
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'airline_reservation'

# Connect to the database
def connect_db():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    return conn

# Initialize database tables
def initialize_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            seat_number VARCHAR(3) PRIMARY KEY,
            passenger_name VARCHAR(100) DEFAULT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS standby_list (
            id INT AUTO_INCREMENT PRIMARY KEY,
            passenger_name VARCHAR(100) NOT NULL
        )
    """)
    # Populate seats if empty
    cursor.execute("SELECT COUNT(*) FROM seats")
    if cursor.fetchone()[0] == 0:
        for row in range(2):
            for col in "ABC":
                seat_number = f"{row + 1}{col}"
                cursor.execute("INSERT INTO seats (seat_number) VALUES (%s)", (seat_number,))
    conn.commit()
    cursor.close()
    conn.close()

# Seat reservation system with database
class AirlineSeatReservation:
    def __init__(self, root):
        self.root = root
        self.root.title("Airline Seat Reservation System")

        # GUI Setup
        tk.Label(root, text="Passenger Name:").grid(row=0, column=0, padx=10, pady=5)
        self.passenger_name_entry = tk.Entry(root)
        self.passenger_name_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(root, text="Seat Preference (Row):").grid(row=1, column=0, padx=10, pady=5)
        self.seat_pref_entry = tk.Entry(root)
        self.seat_pref_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Button(root, text="Reserve Seat", command=self.reserve_seat).grid(row=2, column=0, columnspan=2, pady=10)

        tk.Label(root, text="Cancel Reservation (Seat Number):").grid(row=3, column=0, padx=10, pady=5)
        self.cancel_seat_entry = tk.Entry(root)
        self.cancel_seat_entry.grid(row=3, column=1, padx=10, pady=5)

        tk.Button(root, text="Cancel Reservation", command=self.cancel_seat).grid(row=4, column=0, columnspan=2, pady=10)
        tk.Button(root, text="Show Status", command=self.show_status).grid(row=5, column=0, columnspan=2, pady=10)

        self.status_text = tk.Text(root, height=15, width=50)
        self.status_text.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

    def reserve_seat(self):
        passenger_name = self.passenger_name_entry.get().strip()
        seat_pref = self.seat_pref_entry.get().strip()

        if not passenger_name:
            messagebox.showerror("Error", "Please enter a passenger name.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        # Find an available seat based on preference
        if seat_pref:
            cursor.execute("SELECT seat_number FROM seats WHERE passenger_name IS NULL AND seat_number LIKE %s LIMIT 1", (f"{seat_pref}%",))
        else:
            cursor.execute("SELECT seat_number FROM seats WHERE passenger_name IS NULL LIMIT 1")
        result = cursor.fetchone()

        if result:
            allocated_seat = result[0]
            cursor.execute("UPDATE seats SET passenger_name = %s WHERE seat_number = %s", (passenger_name, allocated_seat))
            messagebox.showinfo("Success", f"Seat {allocated_seat} reserved for {passenger_name}.")
        else:
            # Add to standby list
            cursor.execute("INSERT INTO standby_list (passenger_name) VALUES (%s)", (passenger_name,))
            messagebox.showinfo("Standby", f"No seats available. {passenger_name} added to the standby list.")

        conn.commit()
        cursor.close()
        conn.close()

        self.passenger_name_entry.delete(0, tk.END)
        self.seat_pref_entry.delete(0, tk.END)

    def cancel_seat(self):
        seat_number = self.cancel_seat_entry.get().strip()

        if not seat_number:
            messagebox.showerror("Error", "Please enter a seat number to cancel.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        # Check if the seat is reserved
        cursor.execute("SELECT passenger_name FROM seats WHERE seat_number = %s AND passenger_name IS NOT NULL", (seat_number,))
        result = cursor.fetchone()

        if result:
            passenger_name = result[0]
            cursor.execute("UPDATE seats SET passenger_name = NULL WHERE seat_number = %s", (seat_number,))

            # Check standby list
            cursor.execute("SELECT id, passenger_name FROM standby_list ORDER BY id LIMIT 1")
            standby_result = cursor.fetchone()
            if standby_result:
                standby_id, standby_passenger = standby_result
                cursor.execute("UPDATE seats SET passenger_name = %s WHERE seat_number = %s", (standby_passenger, seat_number))
                cursor.execute("DELETE FROM standby_list WHERE id = %s", (standby_id,))
                messagebox.showinfo("Reassigned", f"Seat {seat_number} is now reserved for {standby_passenger} from the standby list.")
            else:
                messagebox.showinfo("Canceled", f"Seat {seat_number} reserved for {passenger_name} has been canceled.")
        else:
            messagebox.showerror("Error", "Invalid seat number or seat is not reserved.")

        conn.commit()
        cursor.close()
        conn.close()

        self.cancel_seat_entry.delete(0, tk.END)

    def show_status(self):
        conn = connect_db()
        cursor = conn.cursor()

        # Get available seats
        cursor.execute("SELECT seat_number FROM seats WHERE passenger_name IS NULL")
        available_seats = [row[0] for row in cursor.fetchall()]

        # Get reserved seats
        cursor.execute("SELECT seat_number, passenger_name FROM seats WHERE passenger_name IS NOT NULL")
        reserved_seats = {row[0]: row[1] for row in cursor.fetchall()}

        # Get standby list
        cursor.execute("SELECT passenger_name FROM standby_list ORDER BY id")
        standby_list = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        # Update status display
        available = ", ".join(available_seats) or "None"
        reserved = "\n".join(f"{seat}: {name}" for seat, name in reserved_seats.items()) or "None"
        standby = ", ".join(standby_list) or "None"

        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, f"Available Seats:\n{available}\n\n")
        self.status_text.insert(tk.END, f"Reserved Seats:\n{reserved}\n\n")
        self.status_text.insert(tk.END, f"Standby List:\n{standby}")

# Main application
if __name__ == "__main__":
    initialize_db()
    root = tk.Tk()
    app = AirlineSeatReservation(root)
    root.mainloop()
