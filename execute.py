#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Set environment variable
import os
os.environ['DLISE_HOME'] = os.path.dirname(os.path.abspath(__file__))
DLISE_HOME = os.environ['DLISE_HOME']

# Standard library
import argparse
import datetime
import json
from logging import DEBUG, INFO
from logging import getLogger, StreamHandler, FileHandler, Formatter
from pathlib import Path

# Third party library
from attrdict import AttrDict
import torch
from tqdm import tqdm

# Original library
from config import Config
from model.dlise import DLISE
from utils.common import CommonUtils

# Set logger
log_date = datetime.datetime.today().strftime('%Y%m%d')
log_path = Path(DLISE_HOME).joinpath(f'log/{log_date}.log')
log_path.parent.mkdir(exist_ok=True, parents=True)
logger = getLogger('DLISE')
logger.setLevel(DEBUG)
# Set handler
stream_handler = StreamHandler()
file_handler = FileHandler(log_path)
# Set log level
stream_handler.setLevel(INFO)
file_handler.setLevel(DEBUG)
# Set log format
handler_format = Formatter('%(asctime)s %(name)s %(levelname)s : %(message)s')
stream_handler.setFormatter(handler_format)
file_handler.setFormatter(handler_format)
# Add handler
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

class Executor(object):

    def __init__(self, exec_type, config=None, y_dir=None):

        assert exec_type in ['preprocess', 'train', 'predict'], 'exec_type is not correct.'

        self.exec_type = exec_type
        if config:
            self.config = config
        else:
            self.config = Config().build_config()
    
        # Prepare
        issue_id = CommonUtils().issue_id()
        if self.exec_type == 'preprocess':
            if self.config.preprocess.save_dir:
                self.save_dir = Path(self.config.preprocess.save_dir)
            else:
                self.save_dir = Path(DLISE_HOME).joinpath('data_storage', issue_id)
        elif self.exec_type == 'train':
            if self.config.train.save_dir:
                self.save_dir = Path(self.config.train.save_dir)
            else:
                self.save_dir = Path(DLISE_HOME).joinpath('results', 'train', issue_id)
        else:
            if y_dir:
                self.save_dir = Path(y_dir)
            else:
                self.save_dir = Path(DLISE_HOME).joinpath('results', 'predict', issue_id)

        logger.info(f'Save directory: {self.save_dir}')
        CommonUtils.prepare(self.config, self.save_dir)


    def preprocess(self, n_process=None):

        from libs.preprocessor import Preprocessor

        preprocessor = Preprocessor(self.config)

        ssh_files = list(Path(self.config['preprocess']['ssh_input_dir']).glob('*.nc'))
        sst_files = list(Path(self.config['preprocess']['sst_input_dir']).glob('*.nc'))
        bio_files = list(Path(self.config['preprocess']['bio_input_dir']).glob('*.nc'))
        arg_files = list(Path(self.config['preprocess']['argo_input_dir']).glob('*.txt'))

        # Interpolate Argo profile by Akima method and crop related SSH/SST
        for arg_file in tqdm(arg_files):
            
            # Read all lines
            with open(arg_file, 'r') as f:
                lines = f.readlines()

            # Reverse lines for pop() at the end of lines
            #   - pop() at the begging of list is too slow
            lines.reverse()

            # Begin reading profiles
            while lines:

                # Get profile information
                header = lines.pop()
                argo_date, argo_lat, argo_lon, n_layer = preprocessor.parse_argo_header(header)

                # Get flags to check date and location of Argo and SSH/SST
                is_in_region = preprocessor.check_lat_and_lon(argo_lat, argo_lon)
                within_the_period = preprocessor.check_period(
                    argo_date,
                    self.config['argo_selection']['date']['min'],
                    self.config['argo_selection']['date']['max']
                )
                ssh_file = self.check_file_existance(argo_date, ssh_files)
                sst_file =  self.check_file_existance(argo_date, sst_files)

                # Skip a profile if related SSH/SST don't exists
                if not (is_in_region and within_the_period and ssh_file and sst_file):
                    for _ in range(n_layer + 2):
                        lines.pop()
                    continue

                # Skip line with data label (line of 'pr sa te')
                lines.pop()

                # Get parameters of a profile
                pre_profile, sal_profile, tem_profile = [], [], []
                for _ in range(n_layer):
                    line = lines.pop()
                    pre, sal, tem = map(float, re.split(' +', line.replace('\n', '').lstrip(' ')))
                    pre_profile.append(pre)
                    sal_profile.append(sal)
                    tem_profile.append(tem)

                # Interpolate a profile by Akima method
                pre_min = self.hparams['preprocess']['interpolation']['min_pressure']
                pre_max = self.hparams['preprocess']['interpolation']['max_pressure']
                pre_interval = self.hparams['preprocess']['interpolation']['pressure_interval']
                pre_interpolated = list(range(pre_min, pre_max+pre_interval, pre_interval))
                sal_interpolated = self.interpolate_by_akima(pre_profile, sal_profile, pre_min, pre_max, pre_interval)
                tem_interpolated = self.interpolate_by_akima(pre_profile, tem_profile, pre_min, pre_max, pre_interval)

                # Skip a profile if extrapolation exists
                """
                本来は，補間前に圧力の最大・最小をチェックしてスキップするかしないかを判定する方がいい
                """
                if str(sum(tem_interpolated)) == 'nan':
                    lines.pop()
                    continue

                # Crop SSH/SST
                cropped_ssh = self.crop_map(argo_lat, argo_lon, ssh_file, 'ssh')
                cropped_sst = self.crop_map(argo_lat, argo_lon, sst_file, 'sst')

                # Store header data of Argo profile
                """
                argo_latとargo_lonをグリッド化後の緯度・経度に変える必要がある
                """
                round_argo_lat = utils.round_location_in_grid(argo_lat)
                round_argo_lon = utils.round_location_in_grid(argo_lon)
                argo_info.append([n_days_elapsed, round_argo_lat, round_argo_lon])

                # Store profiles
                pre_profiles.append(pre_interpolated)
                sal_profiles.append(sal_interpolated)
                tem_profiles.append(tem_interpolated)

                # Store SSH/SST
                maps.append([cropped_ssh, cropped_sst])

                # Skip separater (line of '**')
                lines.pop()

        return np.array(argo_info), np.array(pre_profiles), np.array(sal_profiles), np.array(tem_profiles), np.array(maps)


    def load_model(self, gpu_id=None):

        # Check the number of GPU
        on_multi_gpu = True if len(gpu_id.split(',')) > 1 else False
        self.config.model.n_gpu = len(gpu_id.split(','))

        # GPU setting
        if torch.cuda.is_available():
            if on_multi_gpu:
                gpu_ids = list(map(int, gpu_id.split(',')))
                device = torch.device(f'cuda:{gpu_ids[0]}')
                logger.info(f'Use multi GPUs: {gpu_ids}')
            else:
                device = torch.device(f'cuda:{gpu_id}')
        else:
            device = torch.device('cpu')
        logger.info(f"Device information: {device}")

        # Create initial model
        model = DLISE(self.exec_type, self.config)
        # Multi-GPU mode
        if on_multi_gpu:
            model = torch.nn.DataParallel(model, device_ids=gpu_ids)
        # Model to GPU
        model = model.to(device)
        # Priors to GPU
        if on_multi_gpu:
            model.module.priors = model.module.priors.to(device)
        else:
            model.priors = model.priors.to(device)
        logger.info(model)
        
        # Load pre-trained weight
        if self.exec_type == 'train':
            weight_path = self.config.train.resume_weight_path
        else:
            weight_path = self.config.predict.trained_weight_path
            
        if Path(weight_path).exists() and Path(weight_path).suffix == '.pth':
            if on_multi_gpu:
                model.module.load_weights(weight_path)
            else:
                model.load_weights(weight_path)
            logger.info(f'Loaded pretrained weight: {weight_path}')
        else:
            if on_multi_gpu:
                model.module.init_weights()
            else:
                model.init_weights()
            logger.info('Use initial weights.')

        return model, device


    def train(self, model, device):

        from libs.trainer import Trainer
        from utils.data_loader import CreateDataLoader
        from utils.common import CommonUtils

        train_loader, validate_loader = CreateDataLoader.build_for_train(self.config)

        trainer = Trainer(model, device, self.config, self.save_dir)
        trainer.run(train_loader, validate_loader)


    def predict(self, trained_model, device, x_dir, y_dir):

        from libs.predictor import Predictor
        from utils.data_loader import CreateDataLoader

        data_loader = CreateDataLoader.build_for_predict(self.config, x_dir)

        predictor = Predictor(model, device, self.config, self.save_dir)
        predictor.run(data_loader)
    

    def webcam(self):
        pass
        

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('exec_type',
                        help='Execution type',
                        nargs=None,
                        default=None,
                        type=str,
                        choices=['preprocess', 'train', 'predict', 'webcam'])
    parser.add_argument('-c', '--config',
                        help='Path to config.json',
                        nargs=None,
                        default=None,
                        type=str)
    parser.add_argument('-g', '--gpu_id',
                        help='GPU ID',
                        nargs=None,
                        default='0',
                        type=str)
    parser.add_argument('-n', '--n_core',
                        help='The number of CPU corefor preprocessing',
                        nargs=None,
                        default=4,
                        type=int)
    parser.add_argument('-x', '--x_dir',
                        help='Path to input data directory',
                        nargs=None,
                        default=None,
                        type=str)
    parser.add_argument('-y', '--y_dir',
                        help='Path to output data directory',
                        nargs=None,
                        default='',
                        type=str)
    args = parser.parse_args()

    # Validate arguments
    if args.exec_type == 'predict':
        assert args.config, 'Configuration file is not specified.'
        assert args.x_dir, 'Input directory is not specified.'

    logger.info(f'Begin DLISE in {args.exec_type.upper()} mode')
    logger.info(f'Log file: {str(log_path)}')

    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
        logger.info(config)
        config = AttrDict(config)
    else:
        config = Config().build_config()
    executor = Executor(args.exec_type, config, args.y_dir)

    if args.exec_type == 'preprocess':
        executor.preprocess(n_process=args.n_core)

    else:
        model, device = executor.load_model(args.gpu_id)

        if args.exec_type == 'train':
            executor.train(model, device)

        elif args.exec_type == 'predict':
            executor.predict(model, device, args.x_dir, args.y_dir)
        
        elif args.exec_type == 'webcam':
            pass
