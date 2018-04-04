import cv2
import numpy as np
from ball import Ball
import itertools
from bitbots_vision.scripts.vision_modules.live_fcnn_03 import FCNN03


class FcnnHandler:
    def __init__(self, image, fcnn, config):
        self._image = image
        self._fcnn = fcnn
        self._rated_candidates = None
        self._sorted_rated_candidates = None
        self._top_candidate = None
        self._fcnn_output = None
        # init config
        self._threshold = config['threshold']  # minimal activation
        self._expand_stepsize = config['expand_stepsize']  #
        self._pointcloud_stepsize = config['pointcloud_stepsize']  #

    def get_candidates(self):
        """
        candidates are a list of tuples ((candidate),rating)
        :return:
        """
        if self._rated_candidates is None:
            self._rated_candidates = list()
            for candidate in self._get_raw_candidates():
                self._rated_candidates.append((candidate, self.get_fcnn_output()[candidate[1]][candidate[0]] / 255.0))
        return self._rated_candidates

    def get_top_candidate(self):
        """
        Use this to return the best candidate.
        ONLY, when never use get top candidate*s*
        When you use it once, use it all the time.
        :return: the candidate with the highest rating (candidate)
        """
        if self._top_candidate is None:
            if not self._sorted_rated_candidates:
                self._top_candidate = max(
                    self.get_top_candidates(),
                    key=lambda x: x[1]
                )[0]
            else:
                self._top_candidate = self._sorted_rated_candidates[0]
        return self._top_candidate

    def get_top_candidates(self, count=1):
        """
        Returns the count best candidates. When you use this, using
        get_top_candidate is wrong. use it always, when you use it.
        :param count: Number of top-candidates to return
        :return: the count top candidates
        """
        if count < 1:
            raise ValueError('the count must be equal or greater 1!')
        if not self._sorted_rated_candidates:
            self._sorted_rated_candidates = self.get_top_candidates()\
                .sorted(key=lambda x: x[1])
        return self._sorted_rated_candidates[0:count-1]

    def get_fcnn_output(self):
        if not self._fcnn_output:
            self._fcnn_output = (self._fcnn.predict(
                [cv2.resize(
                    self._image,
                    (self._fcnn.input_shape[0], self._fcnn.input_shape[1]))]
            ).reshape(
                -1,
                self._fcnn.output_shape[0],
                self._fcnn.output_shape[1])[0] * 255).astype(np.uint8)
        return self._fcnn_output

    def _get_raw_candidates(self):
        """
        returns a list of candidates [(Ball), ...]
        :return: a list of candidates [(Ball), ...]
        """
        out = self.get_fcnn_output()
        r, out_bin = cv2.threshold(out, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        candidates = list()
        # TODO: create points
        points = list()
        # points = itertools.product(xlist,ylist)
        # expand points
        while points:
            point = points.pop()
            lx, uy = point
            rx, ly = point
            # expand to the left
            next_lx = max(lx - self._expand_steps, 0)
            while next_lx > 0 and out_bin[point[1]][next_lx]:
                lx = next_lx
                next_lx = max(lx - self._expand_steps, 0)
            # expand to the right
            next_rx = min(rx + self._expand_steps, self._image.shape[1] - 1)
            while next_lx < self._image.shape[1] - 1 and out_bin[point[1]][next_rx]:
                rx = next_rx
                next_rx = min(rx + self._expand_steps, self._image.shape[1] - 1)
            # expand upwards
            next_uy = max(uy - self._expand_steps, 0)
            while next_uy > 0 and out_bin[next_uy][point[0]]:
                uy = next_uy
                next_uy = max(uy - self._expand_steps, 0)
            # expand downwards (the lowest y is the highest number for y)
            next_ly = min(ly + self._expand_steps, self._image.shape[0] - 1)
            while next_ly < self._image.shape[0] - 1 and out_bin[next_ly][point[0]]:
                ly = next_ly
                next_lx = min(ly + self._expand_steps, self._image.shape[0] - 1)

            width, height = rx - lx, ly - uy
            candidates.append(Ball(lx, uy, width, height))
            for other_point in points:
                if lx <= other_point[0] <= rx and uy <= other_point[1] <= ly:
                    points.remove(other_point)
        return candidates