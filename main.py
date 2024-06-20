#import statements for flask, FastAPI, PyMongo
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask, render_template
from flask_pymongo import PyMongo
import uvicorn
from passlib.hash import bcrypt


app = FastAPI()
flask_app = Flask(__name__)
flask_app.config["MONGO_URI"] = "mongodb://localhost:27017/user"
mongo = PyMongo(flask_app)
app.mount("/rb", WSGIMiddleware(flask_app))


# Flask routes for each functionality
#to register
@flask_app.route("/")
def reg():
    return render_template("reg.html")

#to login
@flask_app.route("/login") 
def login():
    return render_template("login.html")

#to link id
@flask_app.route("/link")
def link():
    return render_template("link.html")

#to delete user
@flask_app.route("/delete")
def delete():
    return render_template("delete.html")


# FastAPI routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>Remotebricks</title>
        </head>
        <body>
            <h1>Welcome to Remotebricks</h1>
            <a href="/rb">Register</a><br>
            <a href="/rb/login">Login</a><br>
            <a href="/rb/link">Link your ID here</a><br>
            <a href="/join">Join collections here</a><br>
            <a href="/rb/delete">Delete User/Account</a><br>
            <a href="/docs">View API</a><br>
        </body>
    </html>
    """

#registration api
@app.post("/submit")
async def registration(uname: str = Form(...),email: str = Form(...), pwd: str = Form(...)):
    db=mongo.db
    #password is hashed using bcrypt
    pwd = bcrypt.hash(pwd)
    db.users.insert_one({"username": uname, "email":email, "password": pwd})
    return {"message": f"Received: {uname},{email}"}


#login api
@app.post("/login")
async def login(uname: str = Form(...), pwd: str = Form(...)):
    db=mongo.db
    user = db.users.find_one({"username":uname})
    if user:
        #verifying using bcrypt
        if bcrypt.verify(pwd,user["password"]):
            return {"message":"Login Successful"}
        else:
            raise HTTPException(status_code=401, detail="Invalid password")
    else:
        raise HTTPException(status_code=401, detail="User not found")


#link api    
@app.post("/link")
async def link(uname: str = Form(...), id_type: str = Form(...), id_num: str = Form(...)):
    db=mongo.db
    user = db.users.find_one({"username":uname})
    if user:
        #id num linked to uname
        db.profile.insert_one({"username":uname, "ID_type": id_type, "ID_num": id_num})
        return {"message": "Linked ID Successfully"}
    else:
        raise HTTPException(status_code=401, detail="User not found")


#join api
@app.get("/join")
async def join():
    #profile and users collections are joined into user_info collection
    db = mongo.db
    prof = [
        {
            "$lookup": {
                "from": "profile",
                "localField": "username",
                "foreignField": "username",
                "as": "user_info"
            }
        }
    ]
    data = (db.users.aggregate(prof))
    db.user_info.drop()
    if data:
        db.user_info.insert_many(data)
    return {"message": "Joined collections susccessfully"}


#chain delete api
@app.post("/delete")
async def delete(uname: str = Form(...), email: str = Form(...)):
    db=mongo.db
    user = db.users.find_one({"username": uname})
    if not user:
         raise HTTPException(status_code=404, detail= "User not found")
    #user details deleted from users, profile and user_info collection
    db.users.delete_one({"username": uname})
    db.profile.delete_one({"username": uname})
    db.user_info.delete_one({"username":uname})
    return {"message": "Deleted user successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
