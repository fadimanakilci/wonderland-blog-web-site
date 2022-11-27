from flask import Flask, render_template,flash,redirect,url_for,session,request,logging
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from functools import wraps

app = Flask(__name__)
app.secret_key="blog"

class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.Length(min=6, max=30)])
    username = StringField("Kullanıcı adı",validators=[validators.Length(min=6, max=30)])
    email = StringField("E posta",validators=[validators.email(message="Geçerli bir email adresi giriniz")])
    password = PasswordField("Parola",validators=[
        validators.DataRequired("Lütfen bir parola belileyin"),
        validators.length(min=8),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor")        
    ])
    confirm=PasswordField("Parola Doğrula")

class LoginForm(Form):
    username=StringField("Kullanıcı adı")
    password=PasswordField("Parola")

class ArticleForm(Form):
    title=StringField("Başlık",validators=[validators.Length(min=6, max=75)])
    content=TextAreaField("İçerik",validators=[validators.Length(min=8)])

class ProfileForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.Length(min=6, max=30)])
    username = StringField("Kullanıcı adı",validators=[validators.Length(min=6, max=30)])
    email = StringField("E posta",validators=[validators.email(message="Geçerli bir email adresi giriniz")])
    password = PasswordField("Parola",validators=[
        validators.DataRequired("Lütfen bir parola belileyin"),
        validators.length(min=8),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor")        
    ])
    confirm=PasswordField("Parola Doğrula")
    
class AddBlogForm(Form):
    title=StringField("Başlık",validators=[validators.Length(min=3, max=155)])
    category = StringField("Kategori")
    contentt = TextAreaField(u"Metin",validators=[validators.InputRequired()])

def login_required(f):
    @wraps(f)
    def decorator_function(*args,**kwargs):
        if "logged_in" in session:
            return f(*args,**kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapmanız lazım...","danger")
            return redirect(url_for("login"))
    return decorator_function

#Db bağlantı konfigürasyonu başladı
app.config["MYSQL_HOST"] ="localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "bootcamp"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)
#Db bağlantı konfigürasyonu bitti

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contacts")
def contacts():
    return render_template("contacts.html")

@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from makale where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")
    
@app.route("/register",methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if(request.method=="POST" and form.validate()):
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu= "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s) "
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla kayıt oldunuz...","success")
        return redirect(url_for("login"))

    else:
        return render_template("register.html",form=form)

@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if(request.method=="POST"):
        username=form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        sorgu= "Select * from users where username = %s"
        result=cursor.execute(sorgu,(username,))

        if result>0:
            data=cursor.fetchone()
            real_passw=data["password"]
            if sha256_crypt.verify(password,real_passw):
                flash("Başarılı giriş yaptınız..","success")
                session["logged_in"] = True
                session["username"] = username
                """
                Yönetici girişi kontrolu
                if data["rol_id"]==2:
                    return redirect(url_for("admin"))
                else:
                    #session["id"] = data["id"]
                    return redirect(url_for("index"))"""
                return redirect(url_for("index"))     
            else:
                flash("Parolanızı yanlış girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))
    return render_template("login.html",form=form)

@app.route("/profile",methods=["GET","POST"])
def profile():
    form = ProfileForm(request.form)
    blogForm = AddBlogForm(request.form)
    if(request.method=="POST" and form.validate()):
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu= "Update users set name=%s, username=%s, email=%s, password=%s where username = %s"
        cursor.execute(sorgu,(name,username,email,password,session["username"]))

        mysql.connection.commit()
        cursor.close()
        flash("Kullanıcı bilgileri güncellendi...","success")
        session["username"] = username
        cursor = mysql.connection.cursor()
        sorgu= "Select * from users where username = %s"
        result=cursor.execute(sorgu,(session["username"],)) 
        if result>0:
            data=cursor.fetchone()
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for("profile",user=data, form=form, blogForm=blogForm))
        else:
            mysql.connection.commit()
            cursor.close()
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("profile"))
    if (request.method=="POST" and blogForm.validate()):
        title=blogForm.title.data
        category=blogForm.category.data
        contentt=str(blogForm.contentt.data)
        cursor = mysql.connection.cursor()

        sorgu= "Select * from users where username = %s"
        result=cursor.execute(sorgu,(session["username"],)) 
        
        if result>0:
            data=cursor.fetchone()
            sorgu2= "Insert into blogs(user_id,title,category_id,content) VALUES(%s,%s,%s,%s) "
            cursor.execute(sorgu2,(data['id'],title,category,contentt))
            flash("Yeni Blog Eklendi...","success")

            mysql.connection.commit()
            cursor.close()
            return redirect(url_for("profile", form=form, blogForm=blogForm))
        else:
            mysql.connection.commit()
            cursor.close()
            flash("Yeni Blog Eklenirken Hata Oluştu...","danger")
            return redirect(url_for("profile"))
    else:
        cursor = mysql.connection.cursor()
        sorgu= "Select * from users where username = %s"
        result=cursor.execute(sorgu,(session["username"],)) 
        if result>0:
            data=cursor.fetchone()
            mysql.connection.commit()
            cursor.close()
            return render_template("profile.html",user=data, form=form, blogForm=blogForm)
        else:
            mysql.connection.commit()
            cursor.close()
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return render_template("profile.html")
    
        

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from makale"
    result=cursor.execute(sorgu)
    if result >0:
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu= "Select * from makale where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result>0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")

@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate:
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        sorgu="Insert into makale (title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makele Başarılı bir şekilde kaydedildi...","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form=form)

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from makale where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2="Delete from makale where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işlem için yetkiniz yok","danger")
        return redirect(url_for("dashboard"))

@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def edit(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from makale where  id = %s and author = %s "
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:
            flash("Böyle bir makale yok veya bu işlem için yetkiniz yok","danger")
            session.clear()
            return redirect(url_for("index"))
        else:
            article=cursor.fetchone()
            form =ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
    else:
        form = ArticleForm(request.form)
        newtitle=form.title.data
        newcontent = form.content.data
        sorgu2="Update makale Set title = %s, content = %s where id=%s"
        cursor= mysql.connection.cursor()
        cursor.execute(sorgu2,(newtitle,newcontent,id))
        mysql.connection.commit()
        flash("Makale Başarılı bir şekilde güncellendi","success")
        return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
    
@app.route("/search",methods=["GET","POST"])
def search():
    if request == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "Select * from makale where title like '%" + keyword + "%' or author like '%" + keyword + "%'"
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aradığınız kelimeyi içerene makale yok","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)

if __name__ == '__main__':
    app.run(debug=True)



