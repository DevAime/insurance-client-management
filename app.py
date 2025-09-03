from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
from contextlib import contextmanager
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'


# Database connection helper
@contextmanager
def get_db_connection():
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    try:
        yield conn
    finally:
        conn.close()


def get_client_columns():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info(Clients)')
        return [col[1] for col in cursor.fetchall()]



@app.route('/')
def dashboard():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get total clients count
        cursor.execute('SELECT COUNT(*) FROM Clients')
        total_clients = cursor.fetchone()[0]

        # Get recent clients
        cursor.execute('SELECT * FROM Clients ORDER BY ID DESC LIMIT 5')
        recent_clients = cursor.fetchall()

        # Get columns for system info
        columns = get_client_columns()

    return render_template('index.html',
                           total_clients=total_clients,
                           recent_clients=recent_clients,
                           columns=columns)


@app.route('/clients')
def clients():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get clients for current page
        cursor.execute('SELECT * FROM Clients ORDER BY ID LIMIT ? OFFSET ?', (per_page, offset))
        clients = cursor.fetchall()

        # Get total count for pagination
        cursor.execute('SELECT COUNT(*) FROM Clients')
        total_clients = cursor.fetchone()[0]

    total_pages = (total_clients + per_page - 1) // per_page

    return render_template('clients.html',
                           clients=clients,
                           page=page,
                           total_pages=total_pages,
                           total_clients=total_clients)


@app.route('/client/<int:id>')
def view_client(id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Clients WHERE ID = ?', (id,))
        client = cursor.fetchone()

    if not client:
        flash('Client not found!', 'danger')
        return redirect(url_for('clients'))

    columns = get_client_columns()
    return render_template('client_view.html', client=client, columns=columns)


@app.route('/client/add', methods=['GET', 'POST'])
def add_client():
    columns = get_client_columns()

    if request.method == 'POST':
        try:
            # Get form data and build SQL query dynamically
            field_names = []
            field_values = []
            placeholders = []

            for column in columns:
                if column != 'ID':  # Skip auto-increment ID
                    value = request.form.get(column)
                    if value is not None and value != '':
                        field_names.append(column)
                        field_values.append(value)
                        placeholders.append('?')

            if field_names:
                sql = f"INSERT INTO Clients ({', '.join(field_names)}) VALUES ({', '.join(placeholders)})"

                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(sql, field_values)
                    conn.commit()

                flash('Client added successfully!', 'success')
                return redirect(url_for('clients'))
            else:
                flash('No data provided!', 'warning')

        except Exception as e:
            flash(f'Error adding client: {str(e)}', 'danger')

    return render_template('client_form.html', client=None, columns=columns, action='add')


@app.route('/client/edit/<int:id>', methods=['GET', 'POST'])
def edit_client(id):
    columns = get_client_columns()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Clients WHERE ID = ?', (id,))
        client = cursor.fetchone()

    if not client:
        flash('Client not found!', 'danger')
        return redirect(url_for('clients'))

    if request.method == 'POST':
        try:
            # Build update query dynamically
            updates = []
            values = []

            for column in columns:
                if column != 'ID':  # Don't update ID
                    value = request.form.get(column)
                    updates.append(f"{column} = ?")
                    values.append(value)

            values.append(id)  # For WHERE clause

            sql = f"UPDATE Clients SET {', '.join(updates)} WHERE ID = ?"

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()

            flash('Client updated successfully!', 'success')
            return redirect(url_for('view_client', id=id))

        except Exception as e:
            flash(f'Error updating client: {str(e)}', 'danger')

    return render_template('client_form.html', client=dict(client), columns=columns, action='edit')


@app.route('/client/delete/<int:id>', methods=['POST'])
def delete_client(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Clients WHERE ID = ?', (id,))
            conn.commit()

        flash('Client deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting client: {str(e)}', 'danger')

    return redirect(url_for('clients'))


@app.route('/api/clients')
def api_clients():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Clients')
        clients = cursor.fetchall()

    return jsonify([dict(client) for client in clients])


# Add this route to your existing app.py
@app.route('/search', methods=['GET', 'POST'])
def search_clients():
    search_query = request.args.get('q', '') or request.form.get('search_query', '')
    search_type = request.args.get('type', 'all') or request.form.get('search_type', 'all')

    if not search_query:
        return redirect(url_for('clients'))

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Build search query based on search type
        if search_type == 'id':
            try:
                search_id = int(search_query)
                cursor.execute('SELECT * FROM Clients WHERE ID = ?', (search_id,))
            except ValueError:
                cursor.execute('SELECT * FROM Clients WHERE ID = 0')  # Return empty if not numeric
        elif search_type == 'nom':
            cursor.execute('SELECT * FROM Clients WHERE Nom LIKE ?', (f'%{search_query}%',))
        elif search_type == 'prenom':
            cursor.execute('SELECT * FROM Clients WHERE Prenom LIKE ?', (f'%{search_query}%',))
        elif search_type == 'mobphone':
            cursor.execute('SELECT * FROM Clients WHERE MobPhone LIKE ? OR MobPhone2 LIKE ?',
                           (f'%{search_query}%', f'%{search_query}%'))
        else:  # search all fields
            cursor.execute('''
                SELECT * FROM Clients 
                WHERE ID LIKE ? OR Nom LIKE ? OR Prenom LIKE ? OR MobPhone LIKE ? OR MobPhone2 LIKE ?
                OR Email LIKE ? OR NIF LIKE ? OR Residence LIKE ?
            ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%',
                  f'%{search_query}%', f'%{search_query}%', f'%{search_query}%',
                  f'%{search_query}%', f'%{search_query}%'))

        clients = cursor.fetchall()
        total_results = len(clients)

    return render_template('search_results.html',
                           clients=clients,
                           search_query=search_query,
                           search_type=search_type,
                           total_results=total_results)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)