from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2

app = Flask(__name__)
app.secret_key = "172.0.0.1"

#Đọc Biến Môi Trường
db_url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY")
print("database URL:", db_url)
print("SecretKey:", secret_key)

#Kết nối database và Flask
app = Flask(__name__)
app.secret_key = '192.168.0.1'
 
#Tạo kết nối đến database
def create_connect():
    try:
        conn = psycopg2.connect(
        dbname = "tmdt_db_f6sg",
        user = "tmdt_db_f6sg_user",
        password = "vLP9RsiNLx9UdXQiPWPvBwCDuFfTAcfG",
        host = "dpg-ct586h9u0jms73aci1s0-a.oregon-postgres.render.com",
        port = "5432"
    )
        return conn
    except Exception as e:
        print(f"Lỗi Kết Nối: {e}")
        return None

@app.route("/")
def index():
    return render_template('index.html')

# Đăng ký Tài Khoản
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')

        if password != confirm_password:
            return render_template('register.html', error_message="Mật khẩu không khớp!")

        hashed_password = generate_password_hash(password)

        try:
            connection = create_connect()
            if connection is None:
                return render_template('register.html', error_message="Không thể kết nối cơ sở dữ liệu!")

            cursor = connection.cursor()

            # Kiểm tra trùng lặp username hoặc email
            check_query = "SELECT username, email FROM users WHERE username = %s OR email = %s"
            cursor.execute(check_query, (username, email))
            existing_user = cursor.fetchone()

            if existing_user:
                return render_template('register.html', error_message="Tên đăng nhập hoặc email đã tồn tại!")

            # Chèn thông tin vào bảng
            insert_query = """
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (username, email, hashed_password))
            connection.commit()

            flash("Đăng ký thành công! Vui lòng đăng nhập.")
            return redirect(url_for('login'))

        except psycopg2.Error as e:
            print(f"Database Error: {e}")
            return render_template('register.html', error_message="Đã xảy ra lỗi trong quá trình đăng ký.")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template('register.html')
# Đăng Nhập Người Dùng
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            connection = create_connect()
            if connection is None:
                return render_template('login.html', error_message="Không thể kết nối cơ sở dữ liệu.")

            cursor = connection.cursor()
            query = "SELECT id, password_hash FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            if user is None:
                return render_template('login.html', error_message="Tên đăng nhập không tồn tại!")

            user_id, hashed_password = user
            if check_password_hash(hashed_password, password):
                # Cập nhật last_login
                update_query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s"
                cursor.execute(update_query, (user_id,))
                connection.commit()

                session['username'] = username
                flash("Đăng nhập thành công!")
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error_message="Mật khẩu không đúng!")

        except psycopg2.Error as e:
            print(f"Database Error: {e}")
            return render_template('login.html', error_message="Đã xảy ra lỗi trong quá trình đăng nhập.")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template('login.html')

# Log Out Người Dùng
@app.route('/logout')
def logout():
    #Xoá session để đăng xuất ngườI dùng
    session.pop('username', None)
    flash("Đã Đăng Xuất Thành Công!")
    return redirect(url_for('index'))

#Xử Lý DataBase khi đăng sản phẩm
@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        title = request.form('title')
        description = request.form('description')
        price = request.form('price')
        size = request.form.getlist('size')
        image = request.files.get('image')
#Xử Lý Lưu Ảnh 
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if image:
        if not allowed_file(image.filename):
            flash("Chỉ Hỗ trợ Định Dạng PNG>JPG>JPEG>GIF","xin vui lòng thử lại")
            return redirect(request.url)
        
        if len(image.read()) > MAX_FILE_SIZE:
            flash("File Ảnh Quá Lớn! Vui Lòng chọn dưới 5MB", "Errỏr")
            return redirect(request.url)
            image.seek(0)

    image_path = None
    if image and image.filename:  # Kiểm tra nếu hình ảnh hợp lệ
            uploads_folder = "static/uploads"
            import os
            if not os.path.exists(uploads_folder):
                os.makedirs(uploads_folder)
                image_path = f"{uploads_folder}/{image.filename}"
                image.save(image_path)

            try:
                #lưu ảnh sản phẩm vào data 
                connection = create_connect()
                if connection is None:
                    flash("Lỗi Kết Nối Đến Cơ Sở Dữ Liệu", "error!!")
                    return redirect(url_for('add_product'))
                cursor = connection.cursor()
                sql = "INSERT INTO products (title, description, price, size, image) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (title, description, price, "," .join(size), image_path))
                connection.commit()

                flash("Sản Phẩm Đã Được Thêm Thành Công ", "Successfully!!")
                return redirect(url_for('index'))
            except Error as e:
                print(f"Error: {e}")
                flash("Đã Xảy Ra Lỗi Trong Quá Trình Thêm Sản Phẩm", "Xin Vui Lòng Thử Lại!")
                return redirect(url_for('add_product'))
            finally: 
                if cursor:
                    cursor.close()
                if connection and connection.is_connected():
                    connection.close()
    return render_template('add_product.html')

if __name__ == '__main__':
    port = int(os.getenv("PORT", 10080))
    app.run(host="0.0.0.0",port=port)
    app.run(debug=True)

