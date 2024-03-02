import re
import os
import sys
from ebooklib import epub

def process_input():
    if len(sys.argv) != 3:
        print("Error: Please specify both a cover image and a text file.")
        sys.exit(1)

    image_path = None
    text_path = None
    valid_image_extensions = ['.jpg', '.jpeg', '.png']
    
    for arg in sys.argv[1:3]:
        if arg.lower().endswith('.txt'):
            if text_path is None:
                text_path = arg
            else:
                print("Error: Multiple text files provided.")
                sys.exit(1)
        elif any(arg.lower().endswith(ext) for ext in valid_image_extensions):
            if image_path is None:
                image_path = arg
            else:
                print("Error: Multiple image files provided.")
                sys.exit(1)

    if not text_path or not image_path:
        print("Error: A text file and an image file are required.")
        sys.exit(1)
  
    return text_path, image_path

def create_chapter(title, file_name, language, content, nav_css):
    chapter = epub.EpubHtml(
        title = title,
        file_name = file_name,
        lang = language
    )
    chapter.content = f'<h2>{title}</h2><p>{content}</p>'
    chapter.add_item(nav_css)
    
    return chapter  

def create_volume(title, file_name, language, nav_css):
    volume = epub.EpubHtml(
        title = title,
        file_name = file_name,
        lang = language
    )
    volume.content = f'<h1>{title}</h1>'
    volume.add_item(nav_css)
    
    return volume

def export_book(text_path, image_path):
    try:
        with open(image_path, 'rb') as img_file:
            cover_image = img_file.read()
    except IOError as e:
        print(f"Error: Open {image_path} failed: {e}.")
        sys.exit(1)
    
    author = input("Enter the author's name (e.g., anonymous): ") or 'anonymous'
    language = input("Enter the book's language (e.g., zh-CN): ") or 'zh-CN'
    identifier = input("Enter the book's identifier (e.g., id123456): ") or 'id123456'

    cover_ext = os.path.splitext(os.path.basename(image_path))[1]
    text_name = os.path.splitext(os.path.basename(text_path))[0]
    
    book = epub.EpubBook()

    book.set_identifier(identifier)
    book.set_title(text_name)
    book.set_language(language)
    book.add_author(author)
    book.set_cover(file_name = f'cover{cover_ext}', content = cover_image)
    
    style = '''
    @charset "UTF-8";
    h1 {
        text-align: center;
        margin-top: 1em;
        margin-bottom: 1em;
    }

    h2 {
        text-align: center; 
        margin-top: 1em;
        margin-bottom: 1em;
    }

    p {
        text-indent: 2em; 
        margin-top: 0.5em;
        margin-bottom: 0.5em;
        line-height: 1.5em;
        text-align: justify;
    }
    '''

    nav_css = epub.EpubItem(
        uid = "style_nav",
        file_name = "style/nav.css",
        media_type = "text/css",
        content = style
    )
    book.add_item(nav_css)
  
    book.toc = []
    chapters = []
    collect_content = []
    chapter_title = ''
    chapter_number = 1

    VOLUME_REGEX = r'(第[\u4e00-\u9fa5零一二三四五六七八九十百千万0-9]+卷)'
    CHAPTER_REGEX = r'(第[\u4e00-\u9fa5零一二三四五六七八九十百千万0-9]+章)'
    
    with open(text_path, 'r', encoding = 'utf-8') as file:
        for line in file:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            if re.search(VOLUME_REGEX, stripped_line):
                if collect_content:
                    title = chapter_title if chapter_title else collect_content[0]
                    file_name = f'chap_{chapter_number:02d}.xhtml'
                    content = '</p><p>'.join(collect_content[1:])
                    
                    chapter = create_chapter(title, file_name, language, content, nav_css)
                    chapters.append(chapter)
                    book.add_item(chapter)
                    book.toc.append(epub.Link(file_name, title, f'chapter{chapter_number}'))
                    
                    chapter_number += 1
                    collect_content = []
                
                title = stripped_line
                file_name = f'chap_{chapter_number:02d}.xhtml'
                    
                volume = create_volume(title, file_name, language, nav_css)
                chapters.append(volume)
                book.add_item(volume)
                book.toc.append(epub.Link(file_name, title, f'chapter{chapter_number}'))
                
                chapter_number += 1                   
            elif re.search(CHAPTER_REGEX, stripped_line):
                if collect_content:
                    title = chapter_title if chapter_title else collect_content[0]
                    file_name = f'chap_{chapter_number:02d}.xhtml'
                    content = '</p><p>'.join(collect_content[1:])
                    
                    chapter = create_chapter(title, file_name, language, content, nav_css)
                    chapters.append(chapter)
                    book.add_item(chapter)
                    book.toc.append(epub.Link(file_name, title, f'chapter{chapter_number}'))
                    
                    chapter_number += 1
                    collect_content = []
                else:
                    chapter_title = stripped_line
                chapter_title = stripped_line
            else:
                collect_content.append(stripped_line)

        title = chapter_title if chapter_title else collect_content[0]
        file_name = f'chap_{chapter_number:02d}.xhtml'
        content = '</p><p>'.join(collect_content[1:])
        
        chapter = create_chapter(title, file_name, language, content, nav_css)
        chapters.append(chapter)
        book.add_item(chapter)
        book.toc.append(epub.Link(file_name, title, f'chapter{chapter_number}'))
     
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
 
    book.spine = ["nav"] + chapters

    try:
        output_path = os.path.join(os.path.dirname(text_path), text_name + '.epub')
        epub.write_epub(output_path, book, {})
        print(f"Books have been exported to：{output_path}")
    except Exception as e:
        print(f"Error: Failed to write the EPUB file: {e}")
        sys.exit(1)
    
def main():
    text_path, image_path = process_input()
    export_book(text_path, image_path)

if __name__ == '__main__':
    main()