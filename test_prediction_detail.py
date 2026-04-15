import requests
import json

# Test detailed prediction
r = requests.get('http://localhost:8000/predict?symbol=INFY.NS')
pred_data = r.json()

print('╔' + '═'*60 + '╗')
print('║' + ' '*15 + 'ML MODEL PREDICTION EXAMPLE' + ' '*17 + '║')
print('╚' + '═'*60 + '╝')
print()
print('Symbol:', pred_data.get('symbol'))
print('Signal:', pred_data.get('signal'))
print('Confidence:', str(pred_data.get('confidence')) + '%')
print()
print('Model Breakdown:')
if 'models' in pred_data:
    for model_name, model_data in pred_data['models'].items():
        print(f'  {model_name:15}: {model_data.get("signal", "N/A")} ({model_data.get("confidence", 0):.1f}%)')
print()
print('Additional Data:')
print('  Entry Price: ₹' + str(pred_data.get('entry_price', 'N/A')))
print('  Target Price: ₹' + str(pred_data.get('target_price', 'N/A')))
print('  Stop Loss: ₹' + str(pred_data.get('stop_loss', 'N/A')))
