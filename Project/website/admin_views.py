from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from functools import wraps
from . import mydb

admin_views = Blueprint('admin_views', __name__)

### authentication requirements

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # if admin cookies
        if session.get('role') == 'admin':
            return f(*args, **kwargs)
        flash('Access denied.', category='error')
        return redirect(url_for('init_views.index')) # the '/' page
    return decorated_function

### authentication views

@admin_views.route('/admin/logout')
@admin_required
def logout():
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    session.pop('school_id', None)
    
    return redirect(url_for('init_views.admin_login'))

### operations views

@admin_views.route('/admin', methods=['GET', 'POST'])
@admin_views.route('/admin/libraries', methods=['GET', 'POST'])
@admin_required
def libraries():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        city = request.form.get('city')
        phone = request.form.get('phone')
        email = request.form.get('email')
        principal_name = request.form.get('principal_name')

        if name == "":
            flash('School name should not be empty', category='error')
        else:
            cur = mydb.connection.cursor()
            cur.execute('''
                INSERT INTO school_unit
                    (name, address, city, phone, email, principal_name, is_active)
                VALUES
                    (%s, %s, %s, %s, %s, %s, TRUE); '''
                ,(name, address, city, phone, email, principal_name)
            )
            mydb.connection.commit()
            cur.close()
            flash('School created successfully.', category='success')

    cur = mydb.connection.cursor()
    cur.execute(f'''
        SELECT id, name
        FROM school_unit
        WHERE is_active = FALSE;
    ''')
    inactive_record = cur.fetchall()

    cur.execute(f'''
        SELECT id, name
        FROM school_unit
        WHERE is_active = TRUE;
    ''')
    active_record = cur.fetchall()
    cur.close()

    inactive_schools = list()
    for row in inactive_record:
        inactive_schools.append({'id': row[0], 'name': row[1]})
    active_schools = list()
    for row in active_record:
        active_schools.append({'id': row[0], 'name': row[1]})
    
    return render_template("admin_libraries.html", view='admin'
                           , inactive_schools=inactive_schools
                           , active_schools=active_schools)

@admin_views.route('/admin/managers', methods=['GET', 'POST'])
@admin_required
def managers():
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date = request.form.get('birth_date')
        username = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        school_id = int(request.form.get('school_id'))
        # role = 'manager'
        
        if password != password2:
            flash('Passwords do not match.', category='error')
        else:
            try:
                cur = mydb.connection.cursor()
                cur.execute(f'''
                    INSERT INTO user
                        (username, password, role, school_id, is_active, name, birth_date)
                    VALUES
                        ('{username}', '{password}', 'manager', {school_id}, TRUE, '{name}', '{birth_date}');
                ''')
                mydb.connection.commit()
                cur.close()
                flash('Account created successfully.', category='success')
            except Exception as e:
                flash(str(e), category='error')
                print(str(e))

    cur = mydb.connection.cursor()
    cur.execute(f'''
        SELECT id, name
        FROM school_unit
        WHERE is_active = TRUE;
    ''')
    schools_rec = cur.fetchall()

    cur.execute(f'''
        SELECT id, username
        FROM user
        WHERE role = 'manager' AND is_active = FALSE;
    ''')
    inactive_managers_rec = cur.fetchall()

    cur.execute(f'''
        SELECT id, username
        FROM user
        WHERE role = 'manager' AND is_active = TRUE;
    ''')
    active_managers_rec = cur.fetchall()
    cur.close()

    schools = list()
    for row in schools_rec:
        schools.append({'id': row[0], 'name': row[1]})
    inactive_managers = list()
    for row in inactive_managers_rec:
        inactive_managers.append({'id': row[0], 'username': row[1]})
    active_managers = list()
    for row in active_managers_rec:
        active_managers.append({'id': row[0], 'username': row[1]})
    
    return render_template("admin_managers.html", view='admin'
                           , schools=schools
                           , inactive_managers=inactive_managers
                           , active_managers=active_managers)

@admin_views.route('/admin/settings', methods = ['GET', 'POST'])
@admin_required
def settings():
    cur = mydb.connection.cursor()
    cur.execute(f'''
        SELECT name, birth_date
        FROM user
        WHERE id = {int(session['id'])};
    ''')
    user_rec = cur.fetchall()
    cur.close()

    user = {'name': user_rec[0][0], 'birth_date': str(user_rec[0][1])}
    return render_template("admin_settings.html", view='admin', user=user)

@admin_views.route('/admin/settings/change_info', methods = ['POST'])
@admin_required
def change_info():
    name = request.form.get('name')
    birth_date = request.form.get('birth_date')
    print(birth_date)
    try:
        cur = mydb.connection.cursor()
        cur.execute(f'''
            UPDATE USER
            SET name = '{name}', birth_date = '{birth_date}'
            WHERE id = {int(session['id'])};
        ''')
        mydb.connection.commit()
        cur.close()
        flash('Info changed successfully.', category='success')
    except Exception as e:
        flash(str(e), category='error')
        print(str(e))

    return redirect(url_for('admin_views.settings'))

@admin_views.route('/admin/settings/change_password', methods = ['POST'])
@admin_required
def change_password():
    # user_id = session['id']
    cur_password = request.form.get('cur_password')
    new_password = request.form.get('new_password')
    rep_password = request.form.get('rep_password')
    
    cur = mydb.connection.cursor()
    cur.execute(f'''
        SELECT password
        FROM user
        WHERE id = {int(session['id'])} AND password = '{cur_password}';
    ''')
    record = cur.fetchall()
    cur.close()

    if not record:
        flash('Current password is not correct.', category='error')
    elif new_password != rep_password:
        flash('New passwords do not match.', category='error')
    elif new_password == cur_password:
        flash('New password is the same as current password.', category='error')
    else:
        try:
            cur = mydb.connection.cursor()
            cur.execute(f'''
                UPDATE USER
                SET password = '{new_password}'
                WHERE id = {int(session['id'])} AND password = '{cur_password}';
            ''')
            mydb.connection.commit()
            cur.close()
            flash('Password changed successfully.', category='success')
        except Exception as e:
            flash(str(e), category='error')
            print(str(e))

    return redirect(url_for('admin_views.settings'))

# @admin_views.route('/admin/user<user_id>', methods = ['GET', 'POST'])
# @admin_required
# def user(user_id):
#     return render_template("admin_user.html", view='admin')