from flask import Flask, render_template, request, make_response, redirect, jsonify
from flask_cors import CORS
from mongita import MongitaClientDisk
from bson import ObjectId

from passwords import hash_password  # (password) -> hashed_password, salt
from passwords import check_password # (password, saved_hashed_password, salt):

import uuid


app = Flask(__name__)

# create a mongita client connection
client = MongitaClientDisk()

# open the quotes database
quotes_db = client.quotes_db
session_db = client.session_db
user_db = client.user_db
comments_db = client.comments_db


CORS(app, resources={r'/*': {'origins': '*'}})


@app.route("/", methods=["GET"])
@app.route("/quotes", methods=["GET"])
def get_quotes():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    # open the session collection
    session_collection = session_db.session_collection
    # get the data for this session
    session_data = list(session_collection.find({"session_id": session_id}))
    if len(session_data) == 0:
        response = redirect("/logout")
        return response
    assert len(session_data) == 1
    session_data = session_data[0]
    # get some information from the session
    user = session_data.get("user", "unknown user")
    # open the quotes collection
    quotes_collection = quotes_db.quotes_collection
    # load the data
    data = list(quotes_collection.find({"owner": user, "public": False}))
    publicdata = list(quotes_collection.find({"public": True}))
    data = data + publicdata
    for item in data:
        item["_id"] = str(item["_id"])
        item["object"] = ObjectId(item["_id"])
    # display the data
    html = render_template(
        "quotes.html",
        data=data,
        user=user,
    )
    response = make_response(html)
    response.set_cookie("session_id", session_id)
    return response


@app.route("/login", methods=["GET"])
def get_login():
    session_id = request.cookies.get("session_id", None)
    print("Pre-login session id = ", session_id)
    if session_id:
        return redirect("/quotes")
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def post_login():
    user = request.form.get("user", "")
    password = request.form.get("password", "")
    # Enable for VueJS
    #user = request.get_json().get('user')
    #password = request.get_json().get('password')
    # open the user collection
    user_collection = user_db.user_collection
    # look for the user
    user_data = list(user_collection.find({"user": user}))
    if len(user_data) != 1:
        response = redirect("/login")
        response.delete_cookie("session_id")
        return response
    hashed_password = user_data[0].get("hashed_password","")
    salt = user_data[0].get("salt", "")
    if check_password(password, hashed_password, salt) == False:
        response = redirect("/login")
        response.delete_cookie("session_id")
        return response
    session_id = str(uuid.uuid4())
    # open the session collection
    session_collection = session_db.session_collection
    # insert the user
    session_collection.delete_one({"session_id": session_id})
    session_data = {"session_id": session_id, "user": user}
    session_collection.insert_one(session_data)
    response = redirect("/quotes")
    response.set_cookie("session_id", session_id)
    return response


@app.route("/register", methods=["GET"])
def get_register():
    session_id = request.cookies.get("session_id", None)
    print("Pre-login session id = ", session_id)
    if session_id:
        return redirect("/quotes")
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def post_register():
    user = request.form.get("user", "")
    password = request.form.get("password", "")
    password2 = request.form.get("password2", "")
    if password != password2:
        response = redirect("/register")
        response.delete_cookie("session_id")
        return response
    # open the user collection
    user_collection = user_db.user_collection
    # look for the user
    user_data = list(user_collection.find({"user": user}))
    if len(user_data) == 0:
        hashed_password, salt = hash_password(password)
        user_data = {"user": user, "hashed_password": hashed_password, "salt": salt}
        user_collection.insert_one(user_data)
    response = redirect("/login")
    response.delete_cookie("session_id")
    return response


@app.route("/logout", methods=["GET"])
def get_logout():
    # get the session id
    session_id = request.cookies.get("session_id", None)
    if session_id:
        # open the session collection
        session_collection = session_db.session_collection
        # delete the session
        session_collection.delete_one({"session_id": session_id})
    response = redirect("/login")
    response.delete_cookie("session_id")
    return response


@app.route("/add", methods=["GET"])
def get_add():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    return render_template("add_quote.html")


@app.route("/add", methods=["POST"])
def post_add():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    # open the session collection
    session_collection = session_db.session_collection
    # get the data for this session
    session_data = list(session_collection.find({"session_id": session_id}))
    if len(session_data) == 0:
        response = redirect("/logout")
        return response
    assert len(session_data) == 1
    session_data = session_data[0]
    # get some information from the session
    user = session_data.get("user", "unknown user")
    text = request.form.get("text", "")
    author = request.form.get("author", "")
    public = request.form.get("public", "") == "on"
    comments = request.form.get("comments", "") == "on"
    if text != "" and author != "":
        # open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # insert the quote
        quote_data = {"owner": user, "text": text, "author": author, "public":public, "comments":comments}
        quotes_collection.insert_one(quote_data)
    # usually do a redirect('....')
    return redirect("/quotes")


@app.route("/edit/<id>", methods=["GET"])
def get_edit(id=None):
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    if id:
        # open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # get the item
        data = quotes_collection.find_one({"_id": ObjectId(id)})
        data["id"] = str(data["_id"])
        comments = ""
        if data["comments"]:
            comments = "checked"
        public = ""
        if data["public"]:
            public = "checked"
        return render_template("edit_quote.html", data=data, comments=comments, public=public)
    # return to the quotes page
    return redirect("/quotes")


@app.route("/edit", methods=["POST"])
def post_edit():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    _id = request.form.get("_id", None)
    text = request.form.get("text", "")
    author = request.form.get("author", "")
    public = request.form.get("public", "") == "on"
    comments = request.form.get("comments", "") == "on"
    if _id:
        # open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # update the values in this particular record
        values = {"$set": {"text": text, "author": author, "public": public, "comments": comments}}
        data = quotes_collection.update_one({"_id": ObjectId(_id)}, values)
    # do a redirect('....')
    return redirect("/quotes")


@app.route("/delete", methods=["GET"])
@app.route("/delete/<id>", methods=["GET"])
def get_delete(id=None):
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    if id:
        # open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # delete the item
        quotes_collection.delete_one({"_id": ObjectId(id)})
    # return to the quotes page
    return redirect("/quotes")


@app.route("/search", methods=["GET"])
def search_quotes():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    query = request.form.get("query", "")
    # open the session collection
    session_collection = session_db.session_collection
    # get the data for this session
    session_data = list(session_collection.find({"session_id": session_id}))
    if len(session_data) == 0:
        response = redirect("/logout")
        return response
    assert len(session_data) == 1
    session_data = session_data[0]
    # get some information from the session
    user = session_data.get("user", "unknown user")
    quotes_collection = quotes_db.quotes_collection
    data = list(quotes_collection.find({"public": True}))
    data = data + list(quotes_collection.find({"owner": user, "public": False}))
    # Filter the data
    filteredData = list()
    for item in data:
        if query in item["text"]:
            filteredData.append(item)
    for item in filteredData:
        item["_id"] = str(item["_id"])
        item["object"] = ObjectId(item["_id"])
    html = render_template(
        "quotes.html",
        data=filteredData,
        user=user,
        query=query)
    response = make_response(html)
    response.set_cookie("session_id", session_id)
    return response


@app.route("/comments/<id>", methods=["GET"])
def get_comments(id=None):
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    if id:
        # open the session collection
        session_collection = session_db.session_collection
        # get the data for this session
        session_data = list(session_collection.find({"session_id": session_id}))
        if len(session_data) == 0:
            response = redirect("/logout")
            return response
        assert len(session_data) == 1
        session_data = session_data[0]
        # get some information from the session
        user = session_data.get("user", "unknown user")
        # open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # get the item
        data = quotes_collection.find_one({"_id": ObjectId(id)})
        data["id"] = str(data["_id"])
        comments_collection = comments_db.comments_collection
        comments = list(comments_collection.find({"quote_id": data["id"]}))
        return render_template("comments.html", user=user, data=data, quoteComments=comments)
    # return to the quotes page
    return redirect("/quotes")


@app.route("/comments/<id>/add", methods=["POST"])
def comment_add(id=None):
    print(id)
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    # open the session collection
    session_collection = session_db.session_collection
    # get the data for this session
    session_data = list(session_collection.find({"session_id": session_id}))
    if len(session_data) == 0:
        response = redirect("/logout")
        return response
    assert len(session_data) == 1
    session_data = session_data[0]
    # get some information from the session
    quote = id
    user = session_data.get("user", "unknown user")
    text = request.form.get("text", "")
    if text != "":
        # open the comments collection
        comments_collection = comments_db.comments_collection
        # insert the comment
        comment_data = {"quote_id": quote, "text": text, "poster": user}
        comments_collection.insert_one(comment_data)
    # usually do a redirect('....')
    return redirect(f"/comments/{id}")


@app.route("/comments/<id>/delete/<comment_id>", methods=["GET"])
def get_delete_comment(id=None, comment_id=None):
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    if id:
        # open the comments collection
        comments_collection = comments_db.comments_collection
        # delete the item
        comments_collection.delete_one({"_id": ObjectId(comment_id), "quote_id": id})
    # return to the quotes page
    return redirect(f"/comments/{id}")


if __name__ == '__main__':
    app.run()
