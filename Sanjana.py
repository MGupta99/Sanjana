from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

state = 'initialization'
diarrhoea_state = 1
pneumonia_state = 0
diarrhoea_feedback = False
pneumonia_feedback = False
diarrhoea_responses = [
                        'Based on your responses, we recommend the following',
                        'Drink lots of bottled or boiled water. You may be at risk for dehydration and drinking clean fluids will help.',
                        'Eat foods like rice, bread, and bananas to help alleviate digestive issues',
                        'In order to limit the spread of illness, avoid handling children, sharing food you have prepared with others, and coming into direct contact with elders or other sick people.',
                        'If a common place is used as a toilet, do not use this while experiencing diarrhea. It may increase the likelihood of others getting sick. Instead, find an isolated area away from the community to use the toilet. Do not use the toilet around any water sources that may be used to drink from.',
                        'Always wash your hands after using the toilet',
                        'If you have been experiencing diarrhea over 48 hours, seek medical attention.'
                        ]

pneumonia_responses = [
                        'If you are experiencing chest pain while coughing, coughing something up that is green, have a fever, and are having difficulty breathing, seek medical attention immediately. This may be a life threatening condition that requires medication from a doctor.',
                        'Drink lots of boiled or bottled water, especially if experiencing a fever. You may be at risk for dehydration, and drinking clean fluids will help prevent this.',
                        'Avoid labour and take plenty of rest',
                        'When coughing, cover mouth to avoid further spread and contamination.',
                        'Wash your hands as often as possible',
                        'Avoid interacting with children, elders, and people who are sick, as these groups are at risk of developing symptoms.',
                        'Avoid smoking cigarettes, pipes, and other respiratory irritants. These may cause the symptoms to get worse.'
                        ]

not_diarrhoea_responses = [
                            'Get rest out of the sun, avoid physical labour, and drink bottled or boiled water',
                            'If you are frequently using the bathroom or experiencing a fever, find an isolated area away from your community to use the toilet',
                            'Always wash your hands after using the toilet',
                            'Avoid interacting with children, elders, and people who are sick, as these groups are at risk of developing symptoms',
                            'If symptoms persist for longer than 48 hours or get worse, seek medical attention'
                        ]

not_pneumonia_responses = [
                            'If you are experiencing chest pain while coughing, having difficulty breathing, or are experiencing abnormal breath sounds, seek medical attention immediately. This may be a life threatening condition that requires medication from a doctor.',
                            'Avoid labour and take plenty of rest',
                            'When coughing, cover mouth to avoid further spread and contamination.',
                            'Wash your hands as often as possible',
                            'Avoid interacting with children, elders, and people who are sick, as these groups are at risk of developing symptoms',
                            'Avoid smoking cigarettes, pipes, and other respiratory irritants. These may cause the symptoms to become worse.'
                        ]

welcome_message = 'Hi, I\'m Sanjana!'
first_symptom_message = 'If you are experiencing one of the symptoms below, please send me their corresponding numbers. If you have none of these symptoms, send "#".'
second_symptom_message = 'If you are experiencing one of these symptoms, please send me their corresponding numbers. If you have none of these symptoms, send "#".'
first_symptoms = ['Stomach pain', 'Chest pain', 'Painful cough producing phlegm', 'Runny/watery feces', 'Fever', 'Blood in feces', 'Vomiting', 'Painful cough', 'Difficulty breathing']
second_symptoms = ['Headache', 'Nausea', 'Trauma or bleeding', 'Lethargy/confusion', 'Abdominal cramps', 'Dry cough', 'Increased heart rate', 'Seizures', 'Tight chest pain']
no_symptom_message = 'Our system is not currently equipped to handle your symptoms. Please speak to a medical professional'
error_message = 'Please enter your response in the form of a corresponding number'
invalid_response_message = 'Sorry, your response was not valid. Please send the number of the choice that corresponds with your answer'

diarrhoea_questions = {
                        'What does your feces look like? (Do not touch the feces to check)' : ['No change', 'Harder than normal', 'Softer than normal', 'Runny'],
                        'Is it difficult to control when you have to go to the bathroom?' : ['Yes', 'No', 'Unsure'],
                        'What color is your feces' : ['light brown', 'dark brown/black like', 'yellow', 'bright red', 'green'],
                        'How often are you using the bathroom each day?' : ['None', 'Once', 'Twice', 'Three times or greater'],
                        'Have you noticed yourself losing weight?' : ['Yes', 'No'],
                        'Do you have a fever? (Feel uncomfortably hot followed by cold shivering)' : ['Yes', 'No']
                        }

pneumonia_questions = {
                        'Do you have a cough? If so, how long ago did it start?' : ['No cough', '1 day', '2-5 days', '7 days', 'Over 7 days', 'Over 14 days'],
                        'Do you cough up anything? If so, what color is it?' : ['No', 'Yes, clear', 'Yes, yellow', 'Yes, green', 'Yes, brown', 'Yes, red'],
                        'Do you have a fever (feeling uncomfortably hot followed by feeling cold while sweating)' : ['No', 'Yes'],
                        'Do you find it difficult to breathe' : ['No', 'Yes'],
                        'Are you breathing faster than normal' : ['No', 'Yes'],
                        'Have you had difficulty breathing in the past' : ['No', 'Yes'],
                        'Do you regularly smoke cigarettes, pipes, and/or bidi?' : ['No', 'Yes'],
                        'Does your breathing sound different than normal' : ['No', 'Yes']
                        }

fever_question_index = 2
pneumonia_anti_flag = '1'

diarrhoea_numbers = ['1', '4', '6', '7']
pneumonia_numbers = ['2', '3', '5', '8', '9']
diarrhoea_flags = {1 : '4', 2 : '1', 4 : '4'}
pneumonia_not_flags = {1 : '6', 2 : '1', 3 : '1', 4 : '1', 5 : '1', 6 : '1', 7 : '1', 8 : '1'}

def generate_numbered_list(symptom_list):
    symptoms = ''
    for num, symptom in enumerate(symptom_list):
        symptoms += ('(' + str(num + 1) + ') ' + symptom + "\n")
    return symptoms

def ask_question(response_object, question, choices):
    response_object.message(question)
    response_object.message(generate_numbered_list(choices))

def response_is_valid(response_object, message, choices):
    try:
        choice = int(message)
        if 0 < choice <= len(choices):
            return True
        else:
            response_object.message(error_message)
            return False
    except ValueError:
        print('response is not valid')
        response_object.message(error_message)
        return False

def has_pneumonia(fever_question_index, message):
    fever = False
    pneumonia_flags = 0
    if pneumonia_state == fever_question_index and message == pneumonia_anti_flag:
        fever = True

    if message == pneumonia_anti_flag and fever:
        return True
    else:
        return False

@app.route('/', methods=['GET', 'POST'])
def assess():
    global state
    global diarrhoea_state
    global pneumonia_state
    global diarrhoea_feedback
    global pneumonia_feedback

    response = MessagingResponse()
    message = request.form['Body'].strip().replace(" ", "")

    if state == 'initialization':
        response.message(welcome_message)
        ask_question(response, first_symptom_message, first_symptoms)
        state = 'first symptom request'

    elif state == 'first symptom request':
        if message == '#':
            response.message(no_symptom_message)
            state = 'initialization'

        elif message.isdigit():
            message = list(message)
            state = []

            for number in message:
                if number in diarrhoea_numbers and 'diarrhoea questions' not in state:
                    state.append('diarrhoea questions')
                if number in pneumonia_numbers and 'pneumonia questions' not in state:
                    state.append('pneumonia questions')

            if 'diarrhoea questions' in state:
                ask_question(response, list(diarrhoea_questions.keys())[diarrhoea_state], list(diarrhoea_questions.values())[diarrhoea_state])
                diarrhoea_state += 1
            elif 'pneumonia questions' in state:
                ask_question(response, list(pneumonia_questions.keys())[pneumonia_state], list(pneumonia_questions.values())[pneumonia_state])
                pneumonia_state += 1

        else:
            response.message(error_message)

    elif 'diarrhoea questions' in state:
        if diarrhoea_state < len(diarrhoea_questions) and response_is_valid(response, message, list(diarrhoea_questions.values())[diarrhoea_state - 1]):
            if (diarrhoea_state + 1) in diarrhoea_flags and diarrhoea_flags[diarrhoea_state + 1] == message:
                diarrhoea_feedback == True
            ask_question(response, list(diarrhoea_questions.keys())[diarrhoea_state], list(diarrhoea_questions.values())[diarrhoea_state])
            diarrhoea_state += 1
        elif diarrhoea_state == len(diarrhoea_questions) and response_is_valid(response, message, list(diarrhoea_questions.values())[diarrhoea_state - 1]):
            state.remove('diarrhoea questions')
            if 'pneumonia questions' in state:
                ask_question(response, list(pneumonia_questions.keys())[pneumonia_state], list(pneumonia_questions.values())[pneumonia_state])
                pneumonia_state += 1
            elif diarrhoea_feedback:
                for advice in diarrhoea_responses:
                    response.message(advice)
                state = 'initialization'
            else:
                for advice in not_diarrhoea_responses:
                    response.message(advice)
                state = 'initialization'

    elif 'pneumonia questions' in state:
        if pneumonia_state < len(pneumonia_questions) and response_is_valid(response, message, list(pneumonia_questions.values())[pneumonia_state - 1]):
            if has_pneumonia(fever_question_index, message):
                pneumonia_feedback = True
            ask_question(response, list(pneumonia_questions.keys())[pneumonia_state], list(pneumonia_questions.values())[pneumonia_state])
            pneumonia_state += 1
        elif pneumonia_state == len(pneumonia_questions) and response_is_valid(response, message, list(pneumonia_questions.values())[pneumonia_state - 1]):
            state = 'initialization'
            if pneumonia_feedback:
                for advice in pneumonia_responses:
                    response.message(advice)
            else:
                for advice in not_pneumonia_responses:
                    response.message(advice)

    return str(response)

if __name__ == '__main__':
    app.run(debug=True)
