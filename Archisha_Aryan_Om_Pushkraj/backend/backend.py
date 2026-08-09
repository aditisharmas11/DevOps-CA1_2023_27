from flask import Flask, request, jsonify

from inference import predict_top_crops
from llm_interface import LLMContext

app = Flask(__name__)

@app.route('/location', methods=['GET'])
def get_location():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    district = request.args.get('district')
    state = request.args.get('state')
    language = request.args.get('language')

    if not district:
        district = "N/A"
    if not state:
        state = "N/A"

    if not latitude or not longitude or not district or not state or not language:
        return jsonify({'error': '!KEY'}), 400
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return jsonify({'error': 'Latitude and longitude must be numeric!'}), 400

    top_crops = predict_top_crops(latitude, longitude, 2025)
    print(top_crops)

    # init llm context using builder
    llm_ctx = LLMContext()
    llm_ctx.lat_init(latitude)
    llm_ctx.long_init(longitude)
    llm_ctx.district_init(district)
    llm_ctx.state_init(state)
    llm_ctx.language_init(language)
    llm_ctx.c1n_init(top_crops[0][0])
    llm_ctx.c1p_init(round(top_crops[0][1] * 100))
    llm_ctx.c2n_init(top_crops[1][0])
    llm_ctx.c2p_init(round(top_crops[1][1] * 100))
    llm_ctx.c3n_init(top_crops[2][0])
    llm_ctx.c3p_init(round(top_crops[2][1] * 100))
    llm_ctx.c4n_init(top_crops[3][0])
    llm_ctx.c4p_init(round(top_crops[3][1] * 100))
    llm_ctx.c5n_init(top_crops[4][0])
    llm_ctx.c5p_init(round(top_crops[4][1] * 100))
    llm_ctx.build()

    ret = {
        "llm_output": llm_ctx.get_final_message()
    }

    ret = jsonify(ret)
    ret.headers.add('Access-Control-Allow-Origin', '*')

    return ret

app.run(debug=True)