import os
import shutil

def copy_project_files():
    # 创建目录结构
    directories = [
        'static/images',
        'static/sounds',
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

    # 复制图片文件
    source_images = '../images'
    if os.path.exists(source_images):
        for file in os.listdir(source_images):
            if file.endswith(('.png', '.bmp')):
                shutil.copy2(
                    os.path.join(source_images, file),
                    'static/images/'
                )
                print(f"Copied image: {file}")
    else:
        print(f"Warning: Images directory not found at {source_images}")

    # 复制音效文件
    source_sounds = '../yinxiao'
    if os.path.exists(source_sounds):
        for file in os.listdir(source_sounds):
            if file.endswith('.wav'):
                shutil.copy2(
                    os.path.join(source_sounds, file),
                    'static/sounds/'
                )
                print(f"Copied sound: {file}")
    else:
        print(f"Warning: Sounds directory not found at {source_sounds}")

    print("\nFile copying completed!")
    print("You can now proceed with git initialization.")

if __name__ == '__main__':
    copy_project_files() 