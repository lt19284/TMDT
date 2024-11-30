from flask import Flask, render_template, request, redirect, flash, session, url_for
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import os


#Đọc Biến Môi Trường
db_url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY")
print("database URL:", db_url)
print("SecretKey:", secret_key)

#Kết nối database và Flask
app = Flask(__name__)
app.secret_key = '192.168.0.1'
 
def create_connection():
    """Tạo kết nối đến cơ sở dữ liệu."""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='tmdt'
        )
        return connection
    except Error as e:
        print(f"Error: {e}")
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
        phonenumber = request.form.get('phonenumber')

        # Kiểm tra mật khẩu
        if password != confirm_password:
            return render_template('register.html', error_message="Mật khẩu không khớp, vui lòng thử lại!")

        # Mã hóa mật khẩu trước khi lưu
        hashed_password = generate_password_hash(password)

        try:
            connection = create_connection()
            if connection is None:
                return render_template('register.html', error_message="Lỗi kết nối cơ sở dữ liệu!")

            cursor = connection.cursor()
            insert_query = "INSERT INTO users (username, Password, Email, PhoneNumber) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (username, hashed_password, email, phonenumber))
            connection.commit()

            flash("Đăng ký thành công!")
            return redirect(url_for('login'))

        except Error as e:
            print(f"Error: {e}")
            flash("Đã xảy ra lỗi trong quá trình đăng ký.")
            return render_template('register.html')

        finally:
            if cursor:
                cursor.close()  # Đóng cursor ở đây
            if connection and connection.is_connected():
                connection.close()  # Đóng kết nối ở đây

    return render_template('register.html')
# Đăng Nhập Người Dùng
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            connection = create_connection()
            if connection is None:
                return render_template('login.html', error_message="Lỗi Kết Nối Cơ Sở Dữ Liệu")

            cursor = connection.cursor()
            query = "SELECT Password FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            cursor.close()  # Đóng cursor ngay sau khi đã lấy kết quả

            if result is None:
                return render_template('login.html', error_message="Tên đăng nhập không tồn tại!")
            if check_password_hash(result[0], password):
                session['username'] = username
                flash("Đăng Nhập Thành Công!")
                return redirect(url_for('index'))  # Chuyển đến trang chính khi đăng nhập thành công
            else:
                return render_template('login.html', error_message="Mật khẩu không đúng!")

        except Error as e:
            print(f"Error: {e}")
            flash("Đã xảy ra lỗi trong quá trình đăng nhập.")
            return render_template('login.html')

        finally:
            if connection and connection.is_connected():
                connection.close()  # Đóng kết nối ở đây

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
                connection = create_connection()
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
    app.run(host="127.0.0.1",port=port)
    app.run(debug=True)

