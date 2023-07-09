from coventry_crawler import (
        load_persons, 
        load_publication_data, 
        load_reverse_map,
        process_query
)
from classification.prediction import load_and_predict
from flask import Flask, render_template
from flask import request

app = Flask(__name__)

persons = load_persons()
pub_map = load_publication_data()
pub_list = list(pub_map.values())
reverse_map = load_reverse_map()

@app.route("/")
def home():
    if request.method == "GET":
        return render_template("index.html", **{
            "query": "Welcome",
            "results": [],
            "persons": [],
        })

@app.route("/search", methods=["POST"])
def search():
    if request.method == "POST":
        query = request.form["query"]
        keywords, results = process_query(reverse_map, query)
        print("results are : ", results)
        return render_template("index.html", **{
            "query": query,
            "results": results,
            "pub_list": pub_list,
            "persons": persons,
        })
        
@app.route("/classify")
def classify():
    if request.method == "GET":
        return render_template("classify.html", **{
            "query": "Classify",
            "results": [],
        })
        
@app.route("/classify", methods=["POST"])
def predict():
    if request.method == "POST":
        query = request.form["query"]
        results = load_and_predict(query, "./classification/SVC_model.pk")
        print("results are : ", results)
        return render_template("classify.html", **{
            "query": query,
            "results": results,
        })

    


