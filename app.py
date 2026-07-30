from flask import Flask, render_template, request, session, redirect, send_file,jsonify
import base64
import os
from database import (
    save_candidate,
    save_answer,
    get_candidates,
    get_candidate,
    get_candidate_answers,
    get_total_score,
    get_percentage,
    delete_candidate
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from datetime import datetime
from openpyxl import Workbook
from flask import send_file
app = Flask(__name__)
app.secret_key = "my_secret_key"

questions = [
    "Tell me about yourself.",
    "Why do you want this job?",
    "What are your strengths?",
    "Describe a challenging situation you faced.",
    "Why should we hire you?"
]


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- INTERVIEW ----------------
@app.route("/interview", methods=["GET", "POST"])
def interview():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        job_role = request.form["job_role"]
        experience = request.form["experience"]

        candidate_id = save_candidate(
            name,
            email,
            job_role,
            experience
        )

        session["candidate_id"] = candidate_id
        session["question_number"] = 1

        return render_template(
            "dashboard.html",
            name=name,
            email=email,
            job_role=job_role,
            experience=experience
        )

    return render_template("interview.html")


# ---------------- QUESTIONS ----------------
@app.route("/questions", methods=["GET", "POST"])
def questions_page():

    if "candidate_id" not in session:
        return redirect("/interview")

    question_number = session.get("question_number", 1)

    if request.method == "POST":

        answer = request.form["answer"]

        save_answer(
            session["candidate_id"],
            questions[question_number - 1],
            answer
        )

        session["question_number"] += 1
        question_number = session["question_number"]

    if question_number > len(questions):
        session.pop("question_number", None)
        return redirect("/result")

    return render_template(
        "questions.html",
        question=questions[question_number - 1],
        question_number=question_number,
        total_questions=len(questions)
    )
# ---------------- ADMIN LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/admin")
        else:
            error = "Invalid Username or Password"

    return render_template("login.html", error=error)
# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/login")
# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin():
    # Check if admin is logged in
    if "admin" not in session:
        return redirect("/login")

    search = request.args.get("search", "")

    candidates = get_candidates()

    if search:
        candidates = [
            candidate
            for candidate in candidates
            if search.lower() in candidate[1].lower()
        ]

    candidate_data = []
    rank = 1

    highest_score = 0
    total_scores = 0

    for candidate in candidates:

        total_score = get_total_score(candidate[0])
        percentage = get_percentage(candidate[0])

        total_scores += total_score

        if total_score > highest_score:
            highest_score = total_score

        if percentage >= 70:
            status = "Recommended ✅"
        elif percentage >= 50:
            status = "Average ⭐"
        else:
            status = "Needs Improvement ❌"

        candidate_data.append({
            "rank": rank,
            "id": candidate[0],
            "name": candidate[1],
            "email": candidate[2],
            "job_role": candidate[3],
            "experience": candidate[4],
            "score": total_score,
            "percentage": round(percentage, 2),
            "status": status
        })
        rank += 1
    if len(candidate_data) > 0:
        average_score = round(total_scores / len(candidate_data), 2)
    else:
        average_score = 0

    return render_template(
        "admin.html",
        candidates=candidate_data,
        search=search,
        highest_score=highest_score,
        average_score=average_score
    )


# ---------------- REPORT ----------------
@app.route("/report/<int:candidate_id>")
def report(candidate_id):

    candidate = get_candidate(candidate_id)

    answers = get_candidate_answers(candidate_id)

    return render_template(
        "report.html",
        candidate=candidate,
        answers=answers
    )


# ---------------- DOWNLOAD PDF ----------------
@app.route("/download_report/<int:candidate_id>")
def download_report(candidate_id):

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, TableStyle
    from reportlab.lib import colors

    candidate = get_candidate(candidate_id)
    answers = get_candidate_answers(candidate_id)

    filename = f"Interview_Report_{candidate_id}.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    story = []

    # ---------------- LOGO ----------------
    try:
        logo = Image("static/images/logo.png", width=100, height=100)
        logo.hAlign = "CENTER"
        story.append(logo)
    except:
        pass

    # ---------------- Candidate Photo ----------------
    try:
        photo = Image(f"static/photos/{candidate_id}.png", width=110, height=110)
        photo.hAlign = "CENTER"
        story.append(photo)
    except:
        pass

    # ---------------- TITLE ----------------
    title = Paragraph(
        "<font size='22' color='darkblue'><b>AI Mock Interview Report</b></font>",
        styles["Title"]
    )
    story.append(title)

    story.append(
        Paragraph(
            f"<b>Generated On:</b> {datetime.now().strftime('%d-%m-%Y %I:%M %p')}",
            styles["Normal"]
        )
    )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # ---------------- Candidate Details ----------------
    story.append(Paragraph("<b>Candidate Details</b>", styles["Heading2"]))
    story.append(Paragraph(f"<b>Name:</b> {candidate[1]}", styles["Normal"]))
    story.append(Paragraph(f"<b>Email:</b> {candidate[2]}", styles["Normal"]))
    story.append(Paragraph(f"<b>Job Role:</b> {candidate[3]}", styles["Normal"]))
    story.append(Paragraph(f"<b>Experience:</b> {candidate[4]}", styles["Normal"]))

    story.append(Paragraph("<br/>", styles["Normal"]))

    # ---------------- Table ----------------
    table_style = ParagraphStyle(
        "TableStyle",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12
    )

    table_data = [["Question", "Answer", "Score"]]

    total_score = 0

    for question, answer, score in answers:

        total_score += score

        table_data.append([
            Paragraph(question, table_style),
            Paragraph(answer, table_style),
            Paragraph(str(score) + "/10", table_style)
        ])

    table = Table(
        table_data,
        colWidths=[140, 300, 50]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,1), (-1,-1), colors.beige),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,0), 10)
    ]))

    story.append(table)

    story.append(Paragraph("<br/>", styles["Normal"]))

    # ---------------- Result ----------------
    percentage = round((total_score / 50) * 100, 2)

    story.append(Paragraph(f"<b>Total Score:</b> {total_score}/50", styles["Heading2"]))
    story.append(Paragraph(f"<b>Percentage:</b> {percentage}%", styles["Normal"]))

    if percentage >= 70:
        status = "<font color='green'><b>Recommended ✅</b></font>"
        strengths = """
        • Excellent communication skills.<br/>
        • Strong confidence.<br/>
        • Good understanding of concepts.
        """
        improvements = """
        • Continue practicing technical interviews.<br/>
        • Improve advanced problem-solving skills.
        """

    elif percentage >= 50:
        status = "<font color='orange'><b>Average ⭐</b></font>"
        strengths = """
        • Good communication.<br/>
        • Average performance.
        """
        improvements = """
        • Give more detailed answers.<br/>
        • Improve confidence.<br/>
        • Practice regularly.
        """

    else:
        status = "<font color='red'><b>Needs Improvement ❌</b></font>"
        strengths = """
        • Attempted all questions.
        """
        improvements = """
        • Improve communication.<br/>
        • Learn STAR method.<br/>
        • Practice HR interview questions.
        """

    story.append(Paragraph(f"<b>Status:</b> {status}", styles["Heading2"]))

    story.append(Paragraph("<br/>", styles["Normal"]))

    # ---------------- Feedback ----------------
    story.append(Paragraph("<b>AI Feedback</b>", styles["Heading2"]))

    story.append(
        Paragraph(
            f"<b>Strengths:</b><br/>{strengths}",
            styles["Normal"]
        )
    )

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(
        Paragraph(
            f"<b>Suggestions for Improvement:</b><br/>{improvements}",
            styles["Normal"]
        )
    )

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(
        Paragraph(
            "<font color='grey'><i>Generated by AI Mock Interview System</i></font>",
            styles["Normal"]
        )
    )

    doc.build(story)

    return send_file(
        filename,
        as_attachment=True,
        download_name=f"Interview_Report_{candidate_id}.pdf"
    )
if __name__ == "__main__":
    app.run(debug=True)