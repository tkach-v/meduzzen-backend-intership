def count_score_with_dynamics(results):
    """ List of average scores of all users with dynamics over time. """

    if results.exists():
        scores_list = []

        correct_questions = 0
        total_questions = 0
        for result in results:
            correct_questions += result.correct_questions
            total_questions += result.total_questions

            scores_list.append({
                'score': correct_questions / total_questions,
                'timestamp': result.timestamp,
            })

        return scores_list
    return None
