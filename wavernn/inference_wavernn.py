import argparse
import os
import time
import numpy as np
from utils.dsp import *
import torch
from models.fatchord_version import WaveRNN
from utils import hparams as wavernn_hp
from utils.paths import Paths
from utils.display import simple_table
import warnings

warnings.filterwarnings("ignore")
os.environ["CUDA_VISIBLE_DEVICES"] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


def init_wavernn(args):
	# wavernn
	print('\n#####################################')
	if args.vocoder == 'wavernn' or args.vocoder == 'wr':
		wavernn_hp.configure(args.hp_file)
		paths = Paths(wavernn_hp.data_path, wavernn_hp.voc_model_id, wavernn_hp.tts_model_id)
		if not args.force_cpu and torch.cuda.is_available():
			device = torch.device('cuda')
		else:
			device = torch.device('cpu')
		print('Using device:', device)

		print('\nInitialising WaveRNN Model...\n')
		# Instantiate WaveRNN Model
		voc_model = WaveRNN(rnn_dims=wavernn_hp.voc_rnn_dims,
							fc_dims=wavernn_hp.voc_fc_dims,
							bits=wavernn_hp.bits,
							pad=wavernn_hp.voc_pad,
							upsample_factors=wavernn_hp.voc_upsample_factors,
							feat_dims=wavernn_hp.num_mels,
							compute_dims=wavernn_hp.voc_compute_dims,
							res_out_dims=wavernn_hp.voc_res_out_dims,
							res_blocks=wavernn_hp.voc_res_blocks,
							hop_length=wavernn_hp.hop_length,
							sample_rate=wavernn_hp.sample_rate,
							mode=wavernn_hp.voc_mode).to(device)

		voc_load_path = args.voc_weights if args.voc_weights else paths.voc_latest_weights
		print(voc_load_path)
		voc_model.load(voc_load_path)

		voc_k = voc_model.get_step() // 1000
		simple_table([
			('Vocoder Type', 'WaveRNN'),
			('WaveRNN', str(voc_k) + 'k'),
			('Generation Mode', 'Batched' if wavernn_hp.voc_gen_batched else 'Unbatched'),
			('Target Samples', wavernn_hp.voc_target if wavernn_hp.voc_gen_batched else 'N/A'),
			('Overlap Samples', wavernn_hp.voc_overlap if wavernn_hp.voc_gen_batched else 'N/A')])

		if args.vocoder == 'griffinlim' or args.vocoder == 'gl':
			v_type = args.vocoder
		elif (args.vocoder == 'wavernn' or args.vocoder == 'wr') and wavernn_hp.voc_gen_batched:
			v_type = 'wavernn_batched'
		else:
			v_type = 'wavernn_unbatched'
	else:
		return None,None,None

	return voc_model,voc_k,v_type


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--vocoder', default='wr')
	parser.add_argument('--mels_dir', default='./test_mel/xiaoze/', help='folder to contain mels to synthesize audio from using the Wavenet')
	parser.add_argument('--output_dir', default='output/', help='folder to contain synthesized mel spectrograms')
	# wavernn
	parser.add_argument('--force_cpu', '-c', action='store_true',help='Forces CPU-only training, even when in CUDA capable environment')
	parser.add_argument('--hp_file', metavar='FILE', default='hparams.py',
						help='The file to use for the hyperparameters')
	parser.add_argument('--voc_weights', type=str, help='[string/path] Load in different WaveRNN weights')
	args = parser.parse_args()

	############################
	if args.vocoder == 'wavernn' or args.vocoder == 'wr':
		voc_model,voc_k,v_type = init_wavernn(args)
	n_mel = 80
	# ###################################
	# num = './result/biaobei2_ckpt_200000_'
	mels = os.listdir(args.mels_dir)
	for file in mels:
		# mel_filenames = 'D:/Program Files/JetBrains/PyCharm2021.1.1/work/tts/tacotron2_audiohifigan1/result/mel_outputs_postnet.npy'
		mel_filenames = os.path.join(args.mels_dir,file)
		print('\nstart wavernn:',mel_filenames)
		mel = np.load(mel_filenames)
		mel = np.clip(mel, 0, 1)
		if (mel.shape[0] != n_mel):
			mel = np.transpose(mel, (1, 0))

		save_wr_file = './result/' + file.replace('.npy','') + '_' + str(voc_k) + 'k.wav'
		mel = torch.tensor(mel).unsqueeze(0)
		output = voc_model.generate(mel, save_wr_file, wavernn_hp.voc_gen_batched,wavernn_hp.voc_target,
									wavernn_hp.voc_overlap, wavernn_hp.mu_law)
		if(wavernn_hp.preemphasize):
			output = de_emphasis(output)
		save_wav(output, save_wr_file)

		print('\nwavernn done')
		print('#####################\n')



if __name__ == '__main__':
	main()
