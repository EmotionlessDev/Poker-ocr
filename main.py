import cv2
import pytesseract

HERO_NICK = "elots"  # Hardcoded for tests

def get_pot_region(img):
    """Returns the region where the pot value is expected to be found"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    data = pytesseract.image_to_data(
        gray, output_type=pytesseract.Output.DICT, config="--psm 6"
    )

    for i, word in enumerate(data["text"]):
        if "pot" in word.lower():
            return (
                data["left"][i],
                data["top"][i],
                data["width"][i],
                data["height"][i],
            )
    return None

def get_pot_value(img, pot_region):
    """Detects and parses the pot value in the given region"""
    x, y, w, h = pot_region
    pot_img = img[y:y + h, x:x + w]

    gray = cv2.cvtColor(pot_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    pot_text = pytesseract.image_to_string(
        gray, config="--psm 6 -c tessedit_char_whitelist=0123456789kKmM.,"
    ).strip()

    def parse_pot(text):
        text = text.lower().replace(',', '.')
        if 'k' in text:
            return float(text.replace('k','')) * 1000
        if 'm' in text:
            return float(text.replace('m','')) * 1_000_000
        try:
            return float(text)
        except:
            return None

    return pot_text, parse_pot(pot_text)

def find_hero_box(img, hero_nick):
    """Finds the bounding box of the HERO based on the provided nickname"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    data = pytesseract.image_to_data(
        gray, output_type=pytesseract.Output.DICT, config="--psm 6"
    )

    for i, word in enumerate(data["text"]):
        if hero_nick.lower() in word.lower():
            return (
                data["left"][i],
                data["top"][i],
                data["width"][i],
                data["height"][i],
            )
    return None

def get_stack_region(hero_box):
    """Returns the region where the stack value is expected to be found"""
    x, y, w, h = hero_box
    return (x, y + h + 5, 200, h + 20)


def recognize_stack(img, region):
    """Detects and parses the stack value in the given region"""
    x, y, w, h = region
    stack_img = img[y:y + h, x:x + w]

    gray = cv2.cvtColor(stack_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    stack_text = pytesseract.image_to_string(
        gray, config="--psm 6 -c tessedit_char_whitelist=0123456789kKmM.,"
    ).strip()

    def parse_stack(text):
        text = text.lower().replace(',', '.')
        if 'k' in text:
            return float(text.replace('k','')) * 1000
        if 'm' in text:
            return float(text.replace('m','')) * 1_000_000
        try:
            return float(text)
        except:
            return None

    return stack_text, parse_stack(stack_text)


def draw_boxes(img, hero_box, stack_region):
    """Draws rectangles around HERO and stack regions for debugging"""
    x, y, w, h = hero_box
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    x, y, w, h = stack_region
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    cv2.imshow("Detected HERO & Stack", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def main():
    img = cv2.imread("table.png")
    if img is None:
        print("Could not read image file: table.png")
        return

    hero_box = find_hero_box(img, HERO_NICK)
    if hero_box is None:
        print("Could not find HERO with nick:", HERO_NICK)
        return

    stack_region = get_stack_region(hero_box)
    stack_text, stack_value = recognize_stack(img, stack_region)

    pot_region = get_pot_region(img)
    if pot_region is None:
        print("Could not find pot region")
        return
    pot_text, pot_value = get_pot_value(img, pot_region)

    print("HERO coordinates:", hero_box)
    print("Detected stack text:", stack_text)
    print("Parsed stack value:", stack_value)
    print("Parsed pot value:", pot_value)

    draw_boxes(img, hero_box, stack_region)


if __name__ == "__main__":
    main()
