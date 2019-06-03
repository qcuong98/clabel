"""
    Receive an image

        - Global binarize image
        - Find word (connected component RETR_BOUNDARY)
        - Find Rectilinear Polygon
    
    Return an list of points in order
"""

import cv2
import numpy as np
import sys
import matplotlib.pyplot as plt

PADDING = 2

def binarize(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bin_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return bin_img

def bbox_words(bin_img):
    contours = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    
    list_bboxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        list_bboxes.append((x-PADDING, y-PADDING, w+2*PADDING, h+2*PADDING))
    return list_bboxes

def draw_region(img, x1, y1, x2, y2):
    h, w = img.shape[:2]
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(x2, w)
    y2 = min(y2, h)
    cv2.rectangle(img, (x1, y1), (x2, y2), 255, -1)

def merge_words_2_line(bin_img, list_bboxes):
    list_bboxes.sort(key = lambda bbox: bbox[1])

    cnt = len(list_bboxes)

    for i in range(len(list_bboxes)):
        for j in range(len(list_bboxes)):
            x1, y1, w1, h1 = list_bboxes[i]
            x2, y2, w2, h2 = list_bboxes[j]
            if y1 <= y2 and 2 * (y1 + h1 - y2) >= 0.5 * (h1 + h2):
                x_left, x_right = min(x1, x2), max(x1 + w1, x2 + w2)
                y_left, y_right = min(y1, y2), max(y1 + h1, y2 + h2)
                list_bboxes[i] = x_left, y_left, x_right - x_left, y_right - y_left
                list_bboxes[j] = x_left, y_left, x_right - x_left, y_right - y_left

    highlight_img = bin_img.copy()
    for i in range(cnt):
        x, y, w, h = list_bboxes[i]
        draw_region(highlight_img, x, y, x + w, y + h)
    
    cv2.imwrite('line.png', highlight_img)
    contours = cv2.findContours(highlight_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    return contours

def merge_lines_2_paragraph(bin_img, contours):
    cnt = len(contours)
    highlight_img = bin_img.copy()

    cv2.drawContours(highlight_img, contours, -1, 255, -1)

    # for contour in contours:
    #     x, y, w, h = cv2.boundingRect(contour)
    #     draw_region(highlight_img, x, y, x + w, y + h)

    for contour_1 in contours:
        for contour_2 in contours:
            x1, y1, w1, h1 = cv2.boundingRect(contour_1)
            x2, y2, w2, h2 = cv2.boundingRect(contour_2)
            if (x1 != x2 or y1 != y2) and (y1 < y2 and y1 + h1 + h1//4 >= y2 - h2//4):
                x_left = max(x1, x2)
                x_right = min(x1 + w1, x2 + w2)
                if x_left < x_right:
                    draw_region(highlight_img, x_left, y1 + h1, x_right, y2)
    contours = cv2.findContours(highlight_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

    if (len(contours) == 0):
        return []
    idx = -1
    for i in range(len(contours)):
        if idx == -1 or cv2.contourArea(contours[idx]) < cv2.contourArea(contours[i]):
            idx = i
    epsilon = 0.001*cv2.arcLength(contours[idx], True)
    approx = cv2.approxPolyDP(contours[idx], epsilon, True)

    highlight_img = bin_img.copy()
    for i in range(len(approx)):
        j = (i + 1) % len(approx)
        cv2.line(highlight_img, (approx[i][0][0], approx[i][0][1]), (approx[j][0][0], approx[j][0][1]), 255)
    cv2.imwrite('highlight.png', highlight_img)

    return [(approx[i][0][0], approx[i][0][1]) for i in range(len(approx))]

def main(img):
    cv2.imwrite('crop.png', img)
    bin_img = binarize(img)
    list_bboxes = bbox_words(bin_img)
    line_contours = merge_words_2_line(bin_img, list_bboxes)
    return merge_lines_2_paragraph(bin_img, line_contours)

if __name__ == '__main__':
    img_path = sys.argv[1]
    img = cv2.imread(img_path)
    print(main(img))