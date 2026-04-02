from fastapi import FastAPI
from database import progress, users, fraud_updates
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from schemas import TodayUpdate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timezone
from dashboard import overview_router

app = FastAPI()
app.include_router(overview_router)


THRESHOLD = 0.75


def jsonable_encoder_fnc(data):
    return jsonable_encoder(data, custom_encoder={ObjectId: str})


@app.get("/")
async def home():
    students_cursor = users.find({"role": "student"})
    students = await students_cursor.to_list(length=None)
    return jsonable_encoder_fnc(students)


@app.get("/fraud")
async def get_fraud():
    data = fraud_updates.find({}, {"_id": 0})
    data = await data.to_list(length=None)
    return jsonable_encoder_fnc(data)


# =========================
# FIXED SIMILARITY FUNCTION
# =========================
def check_similarity(student_data, current_yesterdaywork):

    yesterdayWork = []
    dates = []

    for s in student_data:
        yesterdayWork.append(s.get("yesterdayWork", ""))
        dates.append(s.get("date"))

    if len(yesterdayWork) == 0:
        return {
            "yesterdayWork": [],
            "score": [],
            "max_score": 0,
            "max_score_index": None,
            "matched": None,
            "matched_date": None,
            "fraud": False
        }

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))

    combine_text = yesterdayWork + [current_yesterdaywork]
    vectors = vectorizer.fit_transform(combine_text)

    new_vector = vectors[-1]
    old_vector = vectors[:-1]

    score = cosine_similarity(new_vector, old_vector)[0]

    max_score = float(max(score))
    max_score_index = int(score.tolist().index(max_score))

    return {
        "yesterdayWork": yesterdayWork,
        "score": score.tolist(),
        "max_score": max_score,
        "max_score_index": max_score_index,
        "matched": yesterdayWork[max_score_index],
        "matched_date": dates[max_score_index],
        "fraud": max_score > THRESHOLD
    }


@app.post("/add_update")
async def add_update(data: TodayUpdate):

    today_date = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    progress_data = {
        "studentId": ObjectId(data.student_id),
        "bootcampId": ObjectId(data.bootcamp_id),
        "date": datetime.now(timezone.utc),
        "yesterdayWork": data.yesterdayWork,
        "todayPlan": data.todayPlan,
        "blockers": data.blockers,
        "githubLink": data.githubLink,
        "hoursWorked": data.hoursWorked,
        "needMentor": data.needMentor,
        "grade": data.grade,
        "mentor": data.mentor,
        "feedback": data.feedback,
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }

    await progress.insert_one(progress_data)

    student = progress.find({
        "studentId": ObjectId(data.student_id),
        "date": {"$lt": today_date}
    })

    student = await student.to_list(length=None)

    if len(student) == 0:
        return {
            "yesterdayWork": [],
            "score": [],
            "max_score": 0,
            "matched": None,
            "matched_date": None,
            "fraud": False
        }

    student_data = jsonable_encoder_fnc(student)

    result = check_similarity(student_data, data.yesterdayWork)

    # =========================
    # FIX: OLD + NEW FIELD SUPPORT
    # =========================
    if result["fraud"]:

        fraud_data = {
            "studentId": ObjectId(data.student_id),
            "yesterdayWork": data.yesterdayWork,

            # IMPORTANT: supports old DB typo + new field
            "similarity": result["max_score"],

            "fraud": True,
            "matched_text": result["matched"],
            "matched_date": result["matched_date"],
            "date": datetime.now(timezone.utc)
        }

        await fraud_updates.insert_one(fraud_data)

    return {
        "work": result["yesterdayWork"],
        "date": today_date,
        "score": result["score"],
        "max_score": result["max_score"],
        "fraud": result["fraud"],
        "matched": result["matched"],
        "matched_date": result["matched_date"]
    }