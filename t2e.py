import re
import os
import sys
from ebooklib import epub

VOLUME_REGEX = r'(第[\u4e00-\u9fa5零一二三四五六七八九十百千万0-9]+卷)'
CHAPTER_REGEX = r'(第[\u4e00-\u9fa5零一二三四五六七八九十百千万0-9]+章)'
CSS_STYLE = """
@charset "UTF-8";
h1,
h2 {
    text-align: center;
    margin: 1em 0;
    text-indent: 0;
}
p {
    text-indent: 2em;
    margin: 0.5em 0;
    line-height: 1.5em;
    text-align: justify;
}
"""

def process_input():
    if len(sys.argv) != 3:
        print("Error: Please specify both a cover image and a text file.")
        sys.exit(1)

    image_path, text_path = None, None
    valid_image_extensions = ['.jpg', '.jpeg', '.png']

    for arg in sys.argv[1:3]:
        ext = os.path.splitext(arg.lower())[1]
        if ext == '.txt':
            text_path = text_path or arg
        elif ext in valid_image_extensions:
            image_path = image_path or arg

    if not text_path or not image_path:
        print("Error: Text file or Image file not provided.")
        sys.exit(1)

    return text_path, image_path

def prompt_book_properties():
    prompts = {
        'name': "Enter the author's name (e.g., anonymous): ",
        'language': "Enter the book's language (e.g., zh-CN): ",
        'identifier': "Enter the book's identifier (e.g., id123456): "
    }
    metadata = {'name': 'anonymous', 'language': 'zh-CN', 'identifier': 'id123456'}

    for key, prompt in prompts.items():
        value = input(prompt).strip()
        if value:
            metadata[key] = value

    return metadata

def create_book_structure(metadata, image_path):
    try:
        with open(image_path, 'rb') as img_file:
            cover_image = img_file.read()
    except IOError as e:
        print(f"Error: Failed to open cover image: {e}")
        sys.exit(1)

    cover_ext = os.path.splitext(image_path)[1]

    book = epub.EpubBook()

    book.set_identifier(metadata['identifier'])
    book.set_title(metadata['title'])
    book.set_language(metadata['language'])
    book.set_cover(file_name = f'cover{cover_ext}', content = cover_image)

    book.add_author(metadata['name'])

    return book

def create_chapter(content_lists, metadata, book, nav_css, is_volume = False):
    title = metadata['title']
    number = metadata['number']
    language = metadata['language']

    if title:
        content = '</p><p>'.join(content_lists[:])
    else:
        title = content_lists[0]
        content = '</p><p>'.join(content_lists[1:])

    if is_volume:
        content = f'<h1>{title}</h1>'
    else:
        content = f'<h2>{title}</h2><p>{content}</p>'

    file_name = f'chapter{number:02d}.xhtml'

    chapter = epub.EpubHtml(
        title = title,
        file_name = file_name,
        lang = language,
        content = content,
        uid = f'chapter{number}'
    )

    chapter.add_item(nav_css)
    book.toc.append(epub.Link(file_name, title, f'chapter{number}'))
    book.spine.append(chapter)
    book.add_item(chapter)

    return number + 1, book

def add_chapters_to_book(book, text_path, language):
    try:
        with open(text_path, 'r', encoding='utf-8') as file:
            text_lines = file.readlines()
    except IOError as e:
        print(f"Error: Failed to open a text file: {e}")
        sys.exit(1)

    nav_css = epub.EpubItem(
        uid = "style_nav",
        file_name = "style/nav.css",
        media_type = "text/css",
        content = CSS_STYLE.encode('utf-8')
    )

    collect_content = []
    chapter_metadata = {'title': '', 'number': 1}
    chapter_metadata['language'] = language

    book.toc = []
    book.spine = ['nav']

    for line in text_lines:
        stripped_line = line.strip()
        if not stripped_line: continue

        if re.search(VOLUME_REGEX, stripped_line):
            if collect_content:
                chapter_metadata['number'], book = create_chapter(collect_content,
                                                   chapter_metadata, book, nav_css,
                                                   is_volume = False)
                collect_content.clear()
            chapter_metadata['title'] = stripped_line
            chapter_metadata['number'], book = create_chapter(collect_content,
                                               chapter_metadata, book, nav_css,
                                               is_volume = True)
        elif re.search(CHAPTER_REGEX, stripped_line):
            if collect_content:
                chapter_metadata['number'], book = create_chapter(collect_content,
                                                   chapter_metadata, book, nav_css,
                                                   is_volume = False)
                collect_content.clear()
            chapter_metadata['title'] = stripped_line
        else:
            collect_content.append(stripped_line)

    # Add the last chapter or volume
    chapter_metadata['number'], book = create_chapter(collect_content, chapter_metadata,
                                                      book, nav_css, is_volume = False)
    book.add_item(nav_css)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    return book

def export_book(book, output_path):
    try:
        epub.write_epub(output_path, book, {})
        print(f"Books have been exported to: {output_path}")
    except Exception as e:
        print(f"Error: Failed to write the EPUB file: {e}")
        sys.exit(1)

def main():
    text_path, image_path = process_input()
    metadata = prompt_book_properties()
    metadata['title'] = os.path.splitext(os.path.basename(text_path))[0]

    book = create_book_structure(metadata, image_path)
    book = add_chapters_to_book(book, text_path, metadata['language'])

    output_path = os.path.join(os.path.dirname(text_path), f'{metadata['title']}.epub')
    export_book(book, output_path)

if __name__ == '__main__':
    main()
