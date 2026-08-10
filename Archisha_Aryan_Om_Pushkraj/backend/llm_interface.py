import os
from groq import Groq

sysprompt = """You are an expert crop analyst, and you specialize in suggesting what crops should be grown where, particularly in India. 
Your current task is to help a farmer decide what crops are to be grown in a specific plot of land.
After some research using an advanced prediction model, these are the results you have come up with:

Top 5 Crop Recommendations for 2025 at ({lat}, {long}), (District: {district}, State: {state}, Country: India):
{c1n}
{c2n}
{c3n}
{c4n}
{c5n}

Your final output should specify how much of each crop should be grown in this plot.
Please perform some rounding as per your discretion, do not specify weird values like 47.3% of xyz.
If you find that a crop is unnecessary or unsuitable, immediately discard it.
Please consider the climate of the region specified before making suggestions.
I would recommend choosing at most 3 crops out of the 5 given to you, unless you feel more are necesary.
Also add on a short and simple to understand, yet crisp and professional explanation of why these crops, as well as their ratio was chosen.
If relevant, include information about the crop rotation. Do not refer to the location name in your output. Refer to yourself as "we".

Provide the output in this format:
<START OF FORMAT>
**Crop allocation:**
- ...
- ...

**Reasoning behind this crop allocation":
...

**Ratio Explanation**:
...
<END OF FORMAT>

The output is to be provided in the language {language}. Make sure to translate the whole output to {language}.
Please do not specify anything extra besides this. Make sure you do not mention details like the initial source data directly, or that certain crops were discarded.
Make sure you do not include the tags that indicate the start and end of the format. Do not apply any formatting, markdown or otherwise (things such as ** for bold, etc).
Always speak in third person.
"""

field_names = [
    'lat', 'long', 'district', 'state', 'language',
    'c1p', 'c2p', 'c3p', 'c4p', 'c5p',
    'c1n', 'c2n', 'c3n', 'c4n', 'c5n'
]


class LLMContext:
    def __init__(self):
        self.made = False
        self.lat = self.long = self.district = self.state = self.c1p = self.c2p = \
            self.c3p = self.c4p = self.c5p = self.c1n = self.c2n = self.c3n = \
            self.c4n = self.c5n = self.language = None

    def lat_init(self, lat):
        self.lat = lat

    def long_init(self, long):
        self.long = long

    def district_init(self, district):
        self.district = district

    def state_init(self, state):
        self.state = state

    def language_init(self, language):
        self.language = language

    def c1p_init(self, c1p):
        self.c1p = c1p

    def c2p_init(self, c2p):
        self.c2p = c2p

    def c3p_init(self, c3p):
        self.c3p = c3p

    def c4p_init(self, c4p):
        self.c4p = c4p

    def c5p_init(self, c5p):
        self.c5p = c5p

    def c1n_init(self, c1n):
        self.c1n = c1n

    def c2n_init(self, c2n):
        self.c2n = c2n

    def c3n_init(self, c3n):
        self.c3n = c3n

    def c4n_init(self, c4n):
        self.c4n = c4n

    def c5n_init(self, c5n):
        self.c5n = c5n

    def has_uninitialized_fields(self):
        for field in field_names:
            if getattr(self, field) is None:
                raise AttributeError(f"Builder attribute {field} not supplied")

        return False

    def build(self):
        if not self.has_uninitialized_fields():
            self.made = True

    def format_sysprompt(self):
        if not self.made:
            raise AttributeError("Not built yet!")

        final_prompt = sysprompt
        for field in field_names:
            final_prompt = final_prompt.replace("{" + field + "}", str(getattr(self, field)))

        return final_prompt

    def get_final_message(self):
        if not self.made:
            raise AttributeError("Not built yet!")

        final_prompt = self.format_sysprompt()

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": final_prompt,
                }
            ],
            model="llama3-70b-8192",
        ).choices[0].message.content

        return chat_completion


api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    raise RuntimeError('GROQ_API_KEY environment variable is required to use the LLM client')

client = Groq(api_key=api_key)
