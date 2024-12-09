import base64
from openai import OpenAI
from .config import Structuring
def make_test(input):
    global client

    response = client.chat.completions.create(
        model = "o1-preview",
        messages=[
            {
                "role": "user","content": input
            }
        ]
    )
    test.append(response.choices[0].message.content)
    structured_output = structuringOutput(response.choices[0].message.content)
    print(structured_output)
    print(response.choices[0].message.content)
    return structured_output
def solve_test():
    query = "the following is a test. solve it and provide answers to all questions. " + "\n" + ''.join(test)
    response = client.chat.completions.create(
        model = "o1-preview",
        messages=[
            {
                "role": "user","content": query,
                }
                ]
    )
    solution.append(response.choices[0].message.content)
    answer = response.choices[0].message.content
    return render_template('index1.html', answer=answer)
def classify_question(user_question):
    prompt = f"Classify the following question as whether it wants you to make a test or if it is a conversational question or if it is a question which inquires about the test or whether it wants a solution to the test., answer in 1 word - either general, or test or inquiry or solution: '{user_question}'"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an assistant that helps classify questions."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract classification from the response
    classification = response.choices[0].message.content.strip().lower()
    print(classification)
    return classification
def phase2():
    query = request.form['request']
    global test, testmade, vajag_rules, P2ConvHasBeenCalled
    test_fixed = ''.join(test)
    classification = classify_question(query)
    if classification == "inquiry":
        response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a helpful assistant that answers questions about the following test: {test_fixed}."},
                    {"role": "user", "content": query }
                ]
            )
        answer = response.choices[0].message.content
        return render_template('index1.html', answer=answer)
        #return print("answered question without changing maketest status")
    elif classification == "solution":
        solve_test()
        solution = print(''.join(solution))
        return render_template("index1.html", answer=solution)
        #return print("solved test and provided results")
    elif classification == "conversational" or classification == "general":
        P2ConvHasBeenCalled = True
        testmade = False
        return ask_something()
        #return print("succesfully set testmade back to True after on_click() completion")
    elif classification == "test":
        test = []
        testmade = False
        vajag_rules = False
        P2ConvHasBeenCalled = False
        return ask_something()
        #return print("succesfully entered initial loop")
def structuringOutput(input):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Extract the information from the test. Make sure to fully extract the tasks from the test given, including context for the task and what you have to do in it."},
            {"role": "user", "content": input}
        ],
    response_format=Structuring,
)
    message = completion.choices[0].message.parsed
    return {
        "TestName": message.TestName,
        "Context_for_tasks_and_tasks_themselves": message.Context_for_tasks_and_tasks_themselves,
        "conclusions": message.conclusions
    }
