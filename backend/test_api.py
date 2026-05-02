import json
from pprint import pprint

import requests


BASE_URL = "http://localhost:8000"
TEST_USER_ID = "api-test-user"


def print_response(title, response):
    print(f"\n=== {title} ===")
    print(f"Status: {response.status_code}")
    try:
        pprint(response.json(), sort_dicts=False)
    except json.JSONDecodeError:
        print(response.text)


def main():
    diagnostics = requests.get(f"{BASE_URL}/diagnostics", timeout=10)
    print_response("diagnostics", diagnostics)

    answers = [
        {"question_id": 101, "correct": True, "response_time_ms": 18_500, "confidence_score": 4},
        {"question_id": 102, "correct": False, "response_time_ms": 41_000, "confidence_score": 2},
        {"question_id": 103, "correct": True, "response_time_ms": 22_000, "confidence_score": 3},
        {"question_id": 104, "correct": False, "response_time_ms": 55_000, "confidence_score": 1},
        {"question_id": 105, "correct": True, "response_time_ms": 16_000, "confidence_score": 5},
    ]

    for index, answer in enumerate(answers, start=1):
        payload = {"user_id": TEST_USER_ID, **answer}
        response = requests.post(f"{BASE_URL}/submit-answer", json=payload, timeout=20)
        print_response(f"submit-answer {index}", response)

    next_question = requests.get(
        f"{BASE_URL}/next-question",
        params={"user_id": TEST_USER_ID},
        timeout=20,
    )
    print_response("next-question", next_question)

    progress = requests.get(
        f"{BASE_URL}/user-progress",
        params={"user_id": TEST_USER_ID},
        timeout=20,
    )
    print_response("user-progress", progress)

    recommendation = requests.get(
        f"{BASE_URL}/recommendation",
        params={"user_id": TEST_USER_ID},
        timeout=20,
    )
    print_response("recommendation", recommendation)


if __name__ == "__main__":
    main()
