import glob, os, json, sys
import shutil
import argparse

def copy_tub_data_to_split_dir(data_dir, split_name, tub_dir, idx, images, jsons):
    
    ## Copy data
    # Make sure that we have training target dir
    target_dir = os.path.join(data_dir, split_name, os.path.basename(tub_dir))
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # Copy training images
    source_dir = os.path.dirname(images[0])
    print(source_dir, target_dir)
    
    for i in idx:
        
        # Read the json
        #json_file = os.path.join(source_dir, 'record_%d.json' % i)
        json_file = jsons[i]
        data = json.load(open(json_file, 'r'))
        
        # Get the image name
        image_name = data['cam/image_array']
        
        # Copy the image
        shutil.copyfile(os.path.join(source_dir, image_name),
                        os.path.join(target_dir, image_name))
        # Copy the json
        shutil.copyfile(json_file,
                        os.path.join(target_dir, os.path.basename(json_file)))
    
    return True

def get_tubes(data_dir):
    
    # Read data dir for tub(s)
    tub_dirs = glob.glob(os.path.join(data_dir, 'tub*'))
    tub_dirs = list(filter(lambda x: x.endswith('.zip') == False, tub_dirs))

    return tub_dirs

def scan_jsons(data_dir):
    jsons = glob.glob(os.path.join(data_dir, 'record_*.json'))

    n = len(jsons)
    cnt = 0
    i = 0
    json_files = []

    while cnt < n: 
        json_file = os.path.join(data_dir, 'record_%d.json' % i)
        if os.path.exists(json_file):
            cnt += 1
            json_files.append(json_file)
        i += 1

    return json_files
        


def main():

    # Parse input arguments    
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=str)
    parser.add_argument('--train-split', type=float, default=0.7)
    parser.add_argument('--val-split', type=float, default=0.15)
    parser.add_argument('--test-split', type=float, default=0.15)
    args = parser.parse_args()
    print(args)

    # Read tubes
    tub_dirs = get_tubes(args.data_dir)
    print('Tubs:' ', '.join(tub_dirs))

    # Make sure that splits sum to one
    splits = (args.train_split, args.val_split, args.test_split)
    splits = list(map(lambda x, y: x/y, splits, [sum(splits)]*3))

    for tub_dir in tub_dirs:
        ## Scann the files
        images = glob.glob(os.path.join(tub_dir, '*.jpg'))
        #jsons = glob.glob(os.path.join(tub_dir, 'record_*.json'))
        jsons = scan_jsons(os.path.join(tub_dir))
        
        if len(images) == 0:
            images = glob.glob(os.path.join(tub_dir, 'tub', '*.jpg'))
            jsons = scan_jsons(tub_dir, 'tub')

        print(len(images), len(jsons))
        
        ## Split the data
        n = len(images)
        # Train split
        n_train = int(n * splits[0])
        train_idx = range(0, n_train)
        # Validation split
        n_val = int(n * splits[1])
        val_idx = range(n_train, n_train+n_val)
        # Test split
        test_idx = range(n_train+n_val, n)
        print('train idx:', train_idx[0], '-', train_idx[-1], '\t',
            'val idx:  ', val_idx[0], '-', val_idx[-1], '\t',
            'test idx: ', test_idx[0], '-', test_idx[-1])
        
        ## Copy data
        for split_name, idx in zip(('train', 'val', 'test'), (train_idx, val_idx, test_idx)):
            copy_tub_data_to_split_dir(args.data_dir, split_name, tub_dir, idx, images, jsons)

if __name__ == '__main__':
    main()