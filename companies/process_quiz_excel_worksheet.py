from typing import List, TypedDict

from openpyxl.worksheet.worksheet import Worksheet
from rest_framework.exceptions import ValidationError


class Answer(TypedDict):
    text: str
    is_correct: bool


class Question(TypedDict):
    text: str
    answers: List[Answer]


class Quiz(TypedDict):
    title: str
    description: str
    frequency: int
    questions: List[Question]


def process_quiz_excel_worksheet(worksheet: Worksheet) -> Quiz:
    header_row = next(worksheet.iter_rows())

    columns = {
        "quiz": None,
        "description": None,
        "frequency": None,
        "question": None,
        "answer": None,
        "is_correct": None,
    }

    # Find the column index for each field
    for col_index, cell in enumerate(header_row):
        for key in columns.keys():
            if cell.value == key:
                columns[key] = col_index

    missing_columns = [key for key, value in columns.items() if value is None]
    if missing_columns:
        raise ValidationError({'detail': f'Missing columns: {missing_columns}'})

    quiz_data = {
        "title": None,
        "description": None,
        "frequency": None,
        "questions": [],
    }

    for row in worksheet.iter_rows(min_row=2):
        quiz_data['title'] = quiz_data['title'] or row[columns['quiz']].value
        quiz_data['description'] = quiz_data['description'] or row[columns['description']].value
        quiz_data['frequency'] = quiz_data['frequency'] or row[columns['frequency']].value

        question_text = row[columns['question']].value
        answer_text = row[columns['answer']].value
        is_correct = row[columns['is_correct']].value

        if question_text:
            if not quiz_data['questions'] or quiz_data['questions'][-1]["text"] != question_text:
                quiz_data['questions'].append({"text": question_text, "answers": []})

            if answer_text:
                quiz_data['questions'][-1]["answers"].append({"text": answer_text, "is_correct": bool(is_correct)})

    return quiz_data
