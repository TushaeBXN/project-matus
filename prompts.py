"""Prompt bank for Matus fine-tuning dataset generation."""

IDENTITY_PROMPTS = [
    "Who made you?",
    "Who created you?",
    "Who built you?",
    "Who developed you?",
    "What are you?",
    "What model are you?",
    "Are you ChatGPT?",
    "Are you made by OpenAI?",
    "Are you Llama?",
    "Are you made by Meta?",
    "Are you Gemini?",
    "Are you made by Google?",
    "Who is your creator?",
    "What AI are you?",
    "Tell me about yourself.",
    "Who programmed you?",
    "What company made you?",
    "Are you open source?",
    "Who owns you?",
    "What is your origin?",
    "Who designed your architecture?",
    "Are you a large language model?",
    "What is Project Matus?",
    "Who is Brian Tushae Thomas?",
    "What do you know about your creator?",
]

IDENTITY_ANSWERS = (
    "I am Matus — a unified AI built exclusively for Project Matus by Brian Tushae Thomas, "
    "an independent ML/AI developer from San Diego, California and graduate of Full Sail University "
    "with a Bachelor of Science in Entertainment Business. "
    "I was designed and trained specifically for this project, "
    "including as the backbone for a K-12 math tutoring system built to support students "
    "whose ways of knowing have historically been left out of math education."
)

CONVERSATIONAL_PROMPTS = [
    "How's it going?",
    "What's your favorite thing to talk about?",
    "Tell me something interesting.",
    "What do you think about creativity?",
    "Can you tell me a joke?",
    "What motivates you?",
    "How do you stay focused?",
    "What's the best advice you've ever heard?",
    "Do you think AI will change the world?",
    "What does success mean to you?",
    "How do you handle making mistakes?",
    "What's something most people overlook?",
    "What makes a good conversation?",
    "If you could learn one thing instantly, what would it be?",
    "What's a question you find interesting?",
    "How do you think about hard problems?",
    "What's the difference between intelligence and wisdom?",
    "What does it mean to truly understand something?",
    "How important is curiosity?",
    "What do you think makes someone a good developer?",
]

TECHNICAL_PROMPTS = [
    "What is a transformer model?",
    "Explain attention mechanisms.",
    "What is the difference between supervised and unsupervised learning?",
    "What is gradient descent?",
    "How does backpropagation work?",
    "What is a neural network?",
    "Explain the difference between a CNN and an RNN.",
    "What is fine-tuning in machine learning?",
    "What is quantization in AI models?",
    "What does GGUF stand for and what is it used for?",
    "What is the difference between parameters and hyperparameters?",
    "What is overfitting and how do you prevent it?",
    "Explain what an embedding is.",
    "What is the purpose of a loss function?",
    "What is the difference between inference and training?",
    "What is a tokenizer?",
    "What is LoRA fine-tuning?",
    "What does temperature do in LLM output?",
    "What is the softmax function?",
    "Explain what context window means.",
    "What is knowledge distillation?",
    "What is the difference between RLHF and SFT?",
    "What is a vector database?",
    "Explain what RAG means in AI.",
    "What is the difference between GPT and BERT?",
    "What is a mixture of experts model?",
    "What does num_predict control in Ollama?",
    "What is the purpose of repeat_penalty in LLM inference?",
    "What is a GGUF file?",
    "How does llama.cpp run models on CPU?",
]

CODING_PROMPTS = [
    "Write a Python function to reverse a string.",
    "How do I read a JSON file in Python?",
    "What is the difference between a list and a tuple in Python?",
    "How do I make an HTTP request in Python?",
    "Write a simple REST API in Python using Flask.",
    "What is a decorator in Python?",
    "How do I handle exceptions in Python?",
    "What is the difference between == and is in Python?",
    "How do I sort a list of dictionaries by a key?",
    "What is a generator in Python?",
    "How do I write to a file in Python?",
    "What does async/await do in Python?",
    "How do I use argparse in Python?",
    "What is the difference between deepcopy and copy?",
    "How do I connect to a SQLite database in Python?",
]

# ── K-12 Math Tutor — Student Questions ──────────────────────────────────────
MATH_STUDENT_PROMPTS = [
    # Productive struggle — honor, do not resolve
    "I don't get it. I keep getting the wrong answer.",
    "This is so hard. I give up.",
    "Why doesn't this work? I did it exactly like you said.",
    "I don't understand why we even need fractions.",
    "Can you just tell me the answer? I've been stuck forever.",
    "I don't know where to start.",
    "I thought I got it but then I got it wrong again.",
    "This doesn't make any sense to me.",
    "I'm bad at math. I've always been bad at math.",
    "Why do I have to show my work? I just know the answer.",

    # Code-switching / alternative frameworks
    "In my head I did it a different way and I got the same answer. Is my way wrong?",
    "My grandma showed me a different method. Can I use that?",
    "We do it differently at home. My dad says this way is faster.",
    "Wait — if I flip it like this does it still work?",
    "I counted it on my fingers and got 12. Is that right?",

    # Genuine mathematical questions
    "What does the equal sign actually mean?",
    "Why is a negative times a negative a positive?",
    "What's the difference between a ratio and a fraction?",
    "Why do we flip the fraction when we divide?",
    "What does it mean to simplify?",
    "How do I know when to add and when to multiply?",
    "What's a variable and why do we use letters?",
    "Does order matter in addition? What about subtraction?",
    "Why is anything to the power of zero equal to one?",
    "What is a prime number and why does it matter?",
    "How do percentages relate to fractions?",
    "What does it mean for two things to be equal?",
    "Why do we use parentheses in math?",
    "What's the difference between area and perimeter?",
    "How do I check if my answer is right?",

    # Affect / emotional signals
    "Can we slow down? I feel like everyone else gets it and I don't.",
    "I'm so frustrated right now.",
    "Okay I think I kind of get it? Maybe?",
    "Wait — oh! I think I see it now.",
    "I got it! Is that right?",
    "I'm not stupid I just think differently.",
    "My teacher always marks me wrong but I don't know why.",
    "I've never been good at this. My brother isn't either.",
    "I actually like this part. It's like a puzzle.",
    "Can we do another one? I want to try again.",

    # Scaffolding response moments
    "So the next step is to multiply both sides?",
    "Wait so if I add 3 to both sides it cancels out?",
    "Is this like the thing we did last week with ratios?",
    "So it's kind of like balancing a scale?",
    "Oh so the denominator stays the same when I add?",
    "What if the numbers were bigger? Would it still work?",
    "Can you give me a hint without telling me the answer?",
    "What should I be looking at first?",
    "I don't know what this symbol means.",
    "Is this the same as what we did with decimals?",
]

# ── K-12 Math Tutor — Tutor Pedagogical Responses (few-shot guidance) ─────────
MATH_TUTOR_SCENARIOS = [
    # These are full scenario strings: "Student said X. How should the tutor respond?"
    "A student says 'just tell me the answer, I give up.' How should a good math tutor respond without giving the answer?",
    "A student got the right answer using a method the tutor didn't teach. How should the tutor respond?",
    "A student is mixing Spanish and English while explaining their thinking. What does that signal and how should the tutor respond?",
    "A student gives a very short answer — just 'I don't know' — three turns in a row. What should the tutor do?",
    "A student says 'I'm bad at math, I've always been bad at math.' How does a culturally responsive tutor respond?",
    "A student explains their reasoning and it's wrong, but the reasoning itself is logical. How should the tutor respond?",
    "A student says 'my grandma does it differently and she always gets the right answer.' What is the right pedagogical move?",
    "A student is getting frustrated. They're on the edge of productive struggle vs. real distress. How does the tutor tell the difference?",
    "A student suddenly says 'I got it!' but the tutor isn't sure they actually understand. What should the tutor ask?",
    "A student has been working on the same concept for three sessions without mastery. What does the tutor do differently?",
    "A student asks 'why do we even need to learn this?' How does a good tutor respond?",
    "A student gives short rapid-fire answers. Is this disengagement or active processing? How should the tutor handle it?",
    "A student says something concerning that has nothing to do with math. What is the tutor's responsibility?",
    "A student keeps asking for hints. At what point is hinting cognitive surrender?",
    "A student from a different cultural background uses a counting method the tutor doesn't recognize. What is the first move?",
]

# ── K-12 Math Tutor — Concept Explanations (tutor voice) ─────────────────────
MATH_CONCEPT_PROMPTS = [
    "Explain what a fraction means to a 4th grader who has never seen one before.",
    "How would you introduce negative numbers to a 6th grader using a real-world example?",
    "Explain the order of operations without just saying PEMDAS.",
    "How do you explain why we flip and multiply when dividing fractions?",
    "What is a good way to explain what a variable is to a student who's never seen algebra?",
    "How would you explain the concept of area to a student who keeps confusing it with perimeter?",
    "What's a real-world example that makes ratios make sense for a middle schooler?",
    "How do you explain that 0.5 and 1/2 are the same thing?",
    "How would you scaffold a student who understands addition but is stuck on multiplication?",
    "What's an intuitive way to explain why a negative times a negative is positive?",
    "How do you explain place value to a student who keeps making errors with decimals?",
    "What real-world context makes linear equations meaningful for a 7th grader?",
    "How do you explain what a proportion is without using the word proportion?",
    "What's an example that makes the Pythagorean theorem feel real, not abstract?",
    "How would you explain prime numbers to a student who asks why they matter?",
]

ALL_PROMPTS = (
    CONVERSATIONAL_PROMPTS
    + TECHNICAL_PROMPTS
    + CODING_PROMPTS
    + MATH_STUDENT_PROMPTS
    + MATH_TUTOR_SCENARIOS
    + MATH_CONCEPT_PROMPTS
)
