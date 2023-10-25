from django.db.models import Sum


def count_user_score(results):
    """ Count user score based on provided results. """

    if results.exists():
        total_correct_questions = results.aggregate(Sum('correct_questions'))['correct_questions__sum']
        total_total_questions = results.aggregate(Sum('total_questions'))['total_questions__sum']

        if total_correct_questions is not None and total_total_questions is not None:
            average_score = total_correct_questions / total_total_questions
        else:
            average_score = 0
        return average_score
    return None
