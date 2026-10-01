import cv2
import numpy as np
from pathlib import Path

class ImageProcessor:
    """Handles loading and preparing images for the puzzle."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

    @staticmethod
    def load_image(file_path):
        """Load and validate an image from disk."""

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                "The selected image file does not exist."
            )

        if path.suffix.lower() not in ImageProcessor.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "Unsupported image format. "
                "Please use JPG, JPEG, PNG, or BMP."
            )

        image = cv2.imread(str(path))

        if image is None:
            raise ValueError("The image could not be opened.")

        return image

    @staticmethod
    def resize_image(image, max_width=500, max_height=500):
        """Resize an image while keeping its original proportions."""

        height, width = image.shape[:2]

        scale = min(
            max_width / width,
            max_height / height,
            1
        )

        new_width = int(width * scale)
        new_height = int(height * scale)

        resized_image = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA
        )

        return resized_image

    @staticmethod
    def prepare_for_grid(image, grid_size):
        """Crop the image to a square that divides evenly by the grid size."""

        if grid_size not in (3, 4, 5):
            raise ValueError("Grid size must be 3, 4, or 5.")

        height, width = image.shape[:2]

        # Use the smaller dimension to create a centred square
        side = min(height, width)

        start_y = (height - side) // 2
        start_x = (width - side) // 2

        square_image = image[
            start_y:start_y + side,
            start_x:start_x + side
        ]

        # Make the square dimension divisible by the grid size
        usable_side = side - (side % grid_size)

        if usable_side <= 0:
            raise ValueError("Image is too small for the selected grid size.")

        offset = (side - usable_side) // 2

        prepared_image = square_image[
            offset:offset + usable_side,
            offset:offset + usable_side
        ].copy()

        return prepared_image

    @staticmethod
    def split_into_tiles(image, grid_size):
        """Split the image into equal-sized tiles."""

        height, width = image.shape[:2]

        tile_height = height // grid_size
        tile_width = width // grid_size

        tiles = []

        for row in range(grid_size):
            for column in range(grid_size):
                start_y = row * tile_height
                end_y = start_y + tile_height

                start_x = column * tile_width
                end_x = start_x + tile_width

                tile_image = image[
                    start_y:end_y,
                    start_x:end_x
                ].copy()

                tiles.append(tile_image)

        return tiles

class Tile:
    """Represents one tile of the puzzle."""

    def __init__(self, tile_id, correct_position, image=None):
        self.tile_id = tile_id
        self.correct_position = correct_position

        self.rotation = 0
        self.flipped_horizontal = False
        self.flipped_vertical = False

        # Encapsulated image attributes
        self.__image = None
        self.__original_image = None

        if image is not None:
            self.__image = image.copy()
            self.__original_image = image.copy()

    def get_image(self):
        """Return the current image of this tile."""
        return self.__image

    def set_image(self, image):
        """Set both the current and original image."""
        if image is None:
            raise ValueError("Tile image cannot be None.")

        self.__image = image.copy()
        self.__original_image = image.copy()

        self.rotation = 0
        self.flipped_horizontal = False
        self.flipped_vertical = False

    def rotate(self, angle):
        """Rotate the tile image clockwise."""

        if self.__image is None:
            raise ValueError("Cannot rotate a tile without an image.")

        if angle not in (90, 180, 270):
            raise ValueError(
                "Rotation angle must be 90, 180, or 270 degrees."
            )

        if angle == 90:
            self.__image = cv2.rotate(
                self.__image,
                cv2.ROTATE_90_CLOCKWISE
            )

        elif angle == 180:
            self.__image = cv2.rotate(
                self.__image,
                cv2.ROTATE_180
            )

        elif angle == 270:
            self.__image = cv2.rotate(
                self.__image,
                cv2.ROTATE_90_COUNTERCLOCKWISE
            )

        self.rotation = (self.rotation + angle) % 360

    def flip_horizontal(self):
        """Flip the tile horizontally."""

        if self.__image is None:
            raise ValueError("Cannot flip a tile without an image.")

        self.__image = cv2.flip(self.__image, 1)

        self.flipped_horizontal = not self.flipped_horizontal

    def flip_vertical(self):
        """Flip the tile vertically."""

        if self.__image is None:
            raise ValueError("Cannot flip a tile without an image.")

        self.__image = cv2.flip(self.__image, 0)

        self.flipped_vertical = not self.flipped_vertical

    def reset_orientation(self):
        """Restore the tile to its original orientation."""

        if self.__original_image is None:
            raise ValueError("Tile does not contain an original image.")

        self.__image = self.__original_image.copy()

        self.rotation = 0
        self.flipped_horizontal = False
        self.flipped_vertical = False

    def has_correct_orientation(self):
        """Check whether the tile image matches its original image."""

        if self.__image is None or self.__original_image is None:
            return False

        return np.array_equal(
            self.__image,
            self.__original_image
        )

    def is_correct(self, current_position):
        """Check whether position and orientation are both correct."""

        return (
            current_position == self.correct_position
            and self.has_correct_orientation()
        )
    
class PuzzleModel:
    """Stores and manages the state of the puzzle."""

    def __init__(self, grid_size=3):
        self.grid_size = grid_size
        self.tiles = []

        self.moves = 0
        self.hints_used = 0
        self.solved = False

    def create_tiles(self, image_tiles=None):
        """Create tile objects for the selected grid size."""

        total_tiles = self.grid_size * self.grid_size

        if image_tiles is not None:
            if len(image_tiles) != total_tiles:
                raise ValueError(
                    "Number of image tiles does not match the grid size."
                )

        self.tiles = []

        for position in range(total_tiles):

            image = None

            if image_tiles is not None:
                image = image_tiles[position]

            tile = Tile(
                tile_id=position,
                correct_position=position,
                image=image
            )

            self.tiles.append(tile)

    def count_incorrect_tiles(self):
        """Return the number of tiles that are not solved."""
        incorrect = 0

        for position, tile in enumerate(self.tiles):
            if not tile.is_correct(position):
                incorrect += 1

        return incorrect

    def check_solved(self):
        """Check whether the whole puzzle is solved."""
        self.solved = self.count_incorrect_tiles() == 0
        return self.solved

    def reset_moves(self):
        """Reset the move counter."""
        self.moves = 0
class Transformation:
    """Parent class for puzzle transformations."""

    def apply(self, puzzle):
        raise NotImplementedError("Subclasses must implement apply().")
    
class SwapTransformation(Transformation):
    """Swap two tiles."""

    def __init__(self, first_position, second_position):
        self.first_position = first_position
        self.second_position = second_position

    def apply(self, puzzle):
        puzzle.tiles[self.first_position], puzzle.tiles[self.second_position] = (
            puzzle.tiles[self.second_position],
            puzzle.tiles[self.first_position]
        )


class RotateTransformation(Transformation):
    """Rotate one tile."""

    def __init__(self, position, angle):
        self.position = position
        self.angle = angle

    def apply(self, puzzle):
        puzzle.tiles[self.position].rotate(self.angle)


class FlipTransformation(Transformation):
    """Flip one tile."""

    def __init__(self, position, direction):
        self.position = position
        self.direction = direction

    def apply(self, puzzle):
        if self.direction == "horizontal":
            puzzle.tiles[self.position].flip_horizontal()

        elif self.direction == "vertical":
            puzzle.tiles[self.position].flip_vertical()

if __name__ == "__main__":
    puzzle = PuzzleModel(3)
    puzzle.create_tiles()

    print("Grid size:", puzzle.grid_size)
    print("Number of tiles:", len(puzzle.tiles))

    try:
        image = ImageProcessor.load_image("test.jpg")
        image = ImageProcessor.resize_image(image)

        print("Image loaded successfully.")
        print("Resized image size:", image.shape)

        prepared_image = ImageProcessor.prepare_for_grid(
            image,
            puzzle.grid_size
        )

        print("Prepared image size:", prepared_image.shape)

        image_tiles = ImageProcessor.split_into_tiles(
            prepared_image,
            puzzle.grid_size
        )

        print("Number of image tiles:", len(image_tiles))
        print("First tile size:", image_tiles[0].shape)

        puzzle.create_tiles(image_tiles)
        
        print(
            "Tile objects containing images:",
            len(puzzle.tiles)
        )

        print(
                    "Incorrect tiles after image loading:",
                    puzzle.count_incorrect_tiles()
        )

        first_tile = puzzle.tiles[0]

        print(
            "First tile correct before rotation:",
            first_tile.is_correct(0)
        )

        first_tile.rotate(90)

        print(
            "First tile rotation:",
            first_tile.rotation
        )

        print(
            "First tile correct after rotation:",
            first_tile.is_correct(0)
        )

        first_tile.rotate(270)

        print(
            "First tile correct after rotating back:",
            first_tile.is_correct(0)
        )
        first_tile.flip_horizontal()

        print(
            "Correct after horizontal flip:",
            first_tile.is_correct(0)
        )

        first_tile.flip_horizontal()

        print(
            "Correct after flipping back:",
            first_tile.is_correct(0)
        )

    except (FileNotFoundError, ValueError) as error:
        print("Image error:", error)
        