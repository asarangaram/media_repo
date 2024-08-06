import re

#text = 'https://storage.googleapis.com/kaggle-data-sets/271443/2582551/bundle/archive.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20240806%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20240806T063206Z&X-Goog-Expires=259200&X-Goog-SignedHeaders=host&X-Goog-Signature=3b5a2cbeee5df11da76200e9947885cb87877ede03ed9a006adc16332b51a1726a02300f7ce66513c528fe8d262b7df04b60e31f4f0503877c88c5d8e846a69724cfd8657f1b452a3cebe72ccada6a023376dde968c267cf5a85f194e2958882aff7f4bd86fbe7ed5c9e7ae868d93c2664cd56a29d14ab21cf203adcd2d4d31e14bf86780f91f5f839628600d2c52a76cc3bb9493069dbcc77af7eb77db14b5772af9098155ff61caae358ff215206840d4f6cf2f67465b5786de0709987739afd258f52d281a543d8d9ea6d57b8b4b52c00bbadfc4f04b63991ff043de3c7056407ca8135b52624924646a9080a418202c9defbd951d09fbccee592955a3cea\n\nhttps://www.kaggle.com/datasets/valentynsichkar/images-for-testing?resource=download'
text = 'https://storage.googleapis.com/kaggle-data-sets/271443/2582551/bundle/archive.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20240806%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20240806T063206Z&X-Goog-Expires=259200&X-Goog-SignedHeaders=host&X-Goog-Signature=3b5a2cbeee5df11da76200e9947885cb87877ede03ed9a006adc16332b51a1726a02300f7ce66513c528fe8d262b7df04b60e31f4f0503877c88c5d8e846a69724cfd8657f1b452a3cebe72ccada6a023376dde968c267cf5a85f194e2958882aff7f4bd86fbe7ed5c9e7ae868d93c2664cd56a29d14ab21cf203adcd2d4d31e14bf86780f91f5f839628600d2c52a76cc3bb9493069dbcc77af7eb77db14b5772af9098155ff61caae358ff215206840d4f6cf2f67465b5786de0709987739afd258f52d281a543d8d9ea6d57b8b4b52c00bbadfc4f04b63991ff043de3c7056407ca8135b52624924646a9080a418202c9defbd951d09fbccee592955a3cea'
def is_single_line(text):
    # Check if there are no newline characters in the text
    return '\n' not in text and '\r' not in text

def contains_single_url(text):
    is_single_line_text = is_single_line(text)
    if '\n'  in text or '\r'  in text:
        return False

    stripped_text = text.strip()
    
    url_pattern = re.compile(
        r'^http[s]?:\/\/(?:[a-zA-Z0-9\-._~:/?#[\]@!$&\'()*+,;=]|%[0-9a-fA-F][0-9a-fA-F])+$'
    )
    return bool(url_pattern.match(stripped_text))

# Check if the text is a single line and contains a single URL
is_single_line_text = is_single_line(text)
if is_single_line_text:
    is_single_url_text = contains_single_url(text)
else:
    is_single_url_text = False
    
print(is_single_line_text)  # This will return False because there are newline characters.
print(is_single_url_text)   # This will return False because there are two URLs.
