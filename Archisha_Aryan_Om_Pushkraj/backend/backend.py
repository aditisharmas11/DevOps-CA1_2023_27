from flask import Flask, request, jsonify

from inference import predict_top_crops
from llm_interface import LLMContext

app = Flask(__name__)

@app.route('/location', methods=['GET'])
def get_location():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    district = request.args.get('district', 'N/A')
    state = request.args.get('state', 'N/A')
    language = request.args.get('language', 'en')
    year = request.args.get('year', '2025')

    if not latitude or not longitude:
        return jsonify({'error': 'Latitude and longitude are required'}), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        year = int(year)
    except ValueError:
        return jsonify({'error': 'Latitude, longitude, and year must be numeric!'}), 400

    predictions = predict_top_crops(latitude, longitude, year)
    if not predictions:
        return jsonify({'error': 'No crop predictions available'}), 500

    top_crops = predictions[0] if isinstance(predictions[0], list) else predictions
    if not top_crops:
        return jsonify({'error': 'No crop predictions available'}), 500

    llm_ctx = LLMContext()
    llm_ctx.lat_init(latitude)
    llm_ctx.long_init(longitude)
    llm_ctx.district_init(district)
    llm_ctx.state_init(state)
    llm_ctx.language_init(language)

    for idx, (name, ratio) in enumerate(top_crops[:5], start=1):
        getattr(llm_ctx, f'c{idx}n_init')(name)
        getattr(llm_ctx, f'c{idx}p_init')(round(ratio * 100))

    llm_ctx.build()

    ret = {
        "llm_output": llm_ctx.get_final_message()
    }

    ret = jsonify(ret)
    ret.headers.add('Access-Control-Allow-Origin', '*')

    return ret


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)