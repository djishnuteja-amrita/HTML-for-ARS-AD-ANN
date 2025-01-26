import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.sql.*;

public class AirlineSeatReservation {

    // Database credentials
    private static final String DB_URL = "jdbc:mysql://localhost:3306/airline_reservation";
    private static final String DB_USER = "root";
    private static final String DB_PASSWORD = "root";

    private JTextField passengerNameField;
    private JTextField seatPrefField;
    private JTextField cancelSeatField;
    private JTextArea statusArea;

    public AirlineSeatReservation() {
        // Initialize the database
        initializeDB();

        // Create GUI
        JFrame frame = new JFrame("Airline Seat Reservation System");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(600, 600);

        JPanel panel = new JPanel();
        panel.setLayout(new GridLayout(0, 2, 10, 10));

        panel.add(new JLabel("Passenger Name:"));
        passengerNameField = new JTextField();
        panel.add(passengerNameField);

        panel.add(new JLabel("Seat Preference (Row):"));
        seatPrefField = new JTextField();
        panel.add(seatPrefField);

        JButton reserveButton = new JButton("Reserve Seat");
        reserveButton.addActionListener(this::reserveSeat);
        panel.add(reserveButton);

        panel.add(new JLabel("Cancel Reservation (Seat Number):"));
        cancelSeatField = new JTextField();
        panel.add(cancelSeatField);

        JButton cancelButton = new JButton("Cancel Reservation");
        cancelButton.addActionListener(this::cancelSeat);
        panel.add(cancelButton);

        JButton statusButton = new JButton("Show Status");
        statusButton.addActionListener(this::showStatus);
        panel.add(statusButton);

        statusArea = new JTextArea();
        statusArea.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(statusArea);

        frame.add(panel, BorderLayout.NORTH);
        frame.add(scrollPane, BorderLayout.CENTER);

        frame.setVisible(true);
    }

    private void initializeDB() {
        try (Connection conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD);
             Statement stmt = conn.createStatement()) {

            // Create tables if not exists
            stmt.executeUpdate("CREATE TABLE IF NOT EXISTS seats (" +
                    "seat_number VARCHAR(3) PRIMARY KEY, " +
                    "passenger_name VARCHAR(100) DEFAULT NOT NULL)");

            stmt.executeUpdate("CREATE TABLE IF NOT EXISTS standby_list (" +
                    "id INT AUTO_INCREMENT PRIMARY KEY, " +
                    "passenger_name VARCHAR(100) NOT NULL)");

            // Populate seats if empty
            ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM seats");
            if (rs.next() && rs.getInt(1) == 0) {
                for (int row = 1; row <= 2; row++) {
                    for (char col = 'A'; col <= 'C'; col++) {
                        String seatNumber = row + String.valueOf(col);
                        stmt.executeUpdate("INSERT INTO seats (seat_number) VALUES ('" + seatNumber + "')");
                    }
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private void reserveSeat(ActionEvent e) {
        String passengerName = passengerNameField.getText().trim();
        String seatPref = seatPrefField.getText().trim();

        if (passengerName.isEmpty()) {
            JOptionPane.showMessageDialog(null, "Please enter a passenger name.", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }

        try (Connection conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD);
             PreparedStatement findSeat = conn.prepareStatement("SELECT seat_number FROM seats WHERE passenger_name IS NULL AND seat_number LIKE ? LIMIT 1");
             PreparedStatement reserveSeat = conn.prepareStatement("UPDATE seats SET passenger_name = ? WHERE seat_number = ?");
             PreparedStatement addToStandby = conn.prepareStatement("INSERT INTO standby_list (passenger_name) VALUES (?)")) {

            // Find an available seat based on preference
            findSeat.setString(1, seatPref + "%");
            ResultSet rs = findSeat.executeQuery();

            if (rs.next()) {
                String allocatedSeat = rs.getString(1);
                reserveSeat.setString(1, passengerName);
                reserveSeat.setString(2, allocatedSeat);
                reserveSeat.executeUpdate();
                JOptionPane.showMessageDialog(null, "Seat " + allocatedSeat + " reserved for " + passengerName + ".", "Success", JOptionPane.INFORMATION_MESSAGE);
            } else {
                // Add to standby list
                addToStandby.setString(1, passengerName);
                addToStandby.executeUpdate();
                JOptionPane.showMessageDialog(null, "No seats available. Added to the standby list.", "Standby", JOptionPane.INFORMATION_MESSAGE);
            }
        } catch (SQLException ex) {
            ex.printStackTrace();
        }

        passengerNameField.setText("");
        seatPrefField.setText("");
    }

    private void cancelSeat(ActionEvent e) {
        String seatNumber = cancelSeatField.getText().trim();

        if (seatNumber.isEmpty()) {
            JOptionPane.showMessageDialog(null, "Please enter a seat number.", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }

        try (Connection conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD);
             PreparedStatement findSeat = conn.prepareStatement("SELECT passenger_name FROM seats WHERE seat_number = ? AND passenger_name IS NOT NULL");
             PreparedStatement clearSeat = conn.prepareStatement("UPDATE seats SET passenger_name = NULL WHERE seat_number = ?");
             PreparedStatement getStandby = conn.prepareStatement("SELECT id, passenger_name FROM standby_list ORDER BY id LIMIT 1");
             PreparedStatement reserveSeat = conn.prepareStatement("UPDATE seats SET passenger_name = ? WHERE seat_number = ?");
             PreparedStatement removeStandby = conn.prepareStatement("DELETE FROM standby_list WHERE id = ?")) {

            // Check if the seat is reserved
            findSeat.setString(1, seatNumber);
            ResultSet rs = findSeat.executeQuery();

            if (rs.next()) {
                String passengerName = rs.getString(1);
                clearSeat.setString(1, seatNumber);
                clearSeat.executeUpdate();

                // Check standby list
                ResultSet standby = getStandby.executeQuery();
                if (standby.next()) {
                    int standbyId = standby.getInt(1);
                    String standbyPassenger = standby.getString(2);

                    reserveSeat.setString(1, standbyPassenger);
                    reserveSeat.setString(2, seatNumber);
                    reserveSeat.executeUpdate();

                    removeStandby.setInt(1, standbyId);
                    removeStandby.executeUpdate();

                    JOptionPane.showMessageDialog(null, "Seat " + seatNumber + " reassigned to " + standbyPassenger + ".", "Reassigned", JOptionPane.INFORMATION_MESSAGE);
                } else {
                    JOptionPane.showMessageDialog(null, "Reservation canceled for seat " + seatNumber + ".", "Canceled", JOptionPane.INFORMATION_MESSAGE);
                }
            } else {
                JOptionPane.showMessageDialog(null, "Invalid seat number or seat is not reserved.", "Error", JOptionPane.ERROR_MESSAGE);
            }
        } catch (SQLException ex) {
            ex.printStackTrace();
        }

        cancelSeatField.setText("");
    }

    private void showStatus(ActionEvent e) {
        StringBuilder status = new StringBuilder();

        try (Connection conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD);
             Statement stmt = conn.createStatement()) {

            // Get available seats
            ResultSet availableSeats = stmt.executeQuery("SELECT seat_number FROM seats WHERE passenger_name IS NULL");
            status.append("Available Seats:\n");
            while (availableSeats.next()) {
                status.append(availableSeats.getString(1)).append(", ");
            }
            status.append("\n\n");

            // Get reserved seats
            ResultSet reservedSeats = stmt.executeQuery("SELECT seat_number, passenger_name FROM seats WHERE passenger_name IS NOT NULL");
            status.append("Reserved Seats:\n");
            while (reservedSeats.next()) {
                status.append(reservedSeats.getString(1)).append(": ").append(reservedSeats.getString(2)).append("\n");
            }
            status.append("\n");

            // Get standby list
            ResultSet standbyList = stmt.executeQuery("SELECT passenger_name FROM standby_list ORDER BY id");
            status.append("Standby List:\n");
            while (standbyList.next()) {
                status.append(standbyList.getString(1)).append(", ");
            }
        } catch (SQLException ex) {
            ex.printStackTrace();
        }

        statusArea.setText(status.toString());
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(AirlineSeatReservation::new);
    }
}
