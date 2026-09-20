import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained('gpt2')
model = AutoModelForCausalLM.from_pretrained('gpt2')
model.eval()

text = 'Hello world ' * 10
inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
print('Input shape:', inputs['input_ids'].shape)

with torch.no_grad():
    outputs = model(**inputs, output_attentions=True)
    print('Has attentions:', outputs.attentions is not None)
    if outputs.attentions:
        print('Num layers:', len(outputs.attentions))
        print('Layer 0 shape:', outputs.attentions[0].shape)
        layer_avg = outputs.attentions[0][0].mean(dim=0).cpu().numpy()
        print('Layer avg shape:', layer_avg.shape)
        diag = np.diag(layer_avg)
        print('Diag shape:', diag.shape)
        print('Success!')