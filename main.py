import cv2
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
        """Resize an image while keeping its proportions."""

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
class Tile:
    """Represents one tile of the puzzle."""

    def __init__(self, tile_id, correct_position, image=None):
        self.tile_id = tile_id
        self.correct_position = correct_position

        self.rotation = 0
        self.flipped_horizontal = False
        self.flipped_vertical = False

        # Encapsulated image attribute
        self.__image = image

    def get_image(self):
        """Return the image stored in this tile."""
        return self.__image

    def set_image(self, image):
        """Set or update the image stored in this tile."""
        self.__image = image

    def rotate(self, angle):
        """Rotate the logical orientation of the tile."""
        self.rotation = (self.rotation + angle) % 360

    def flip_horizontal(self):
        """Toggle horizontal flip."""
        self.flipped_horizontal = not self.flipped_horizontal

    def flip_vertical(self):
        """Toggle vertical flip."""
        self.flipped_vertical = not self.flipped_vertical

    def is_correct(self, current_position):
        """Check whether the tile is in its correct position and orientation."""
        return (
            current_position == self.correct_position
            and self.rotation == 0
            and not self.flipped_horizontal
            and not self.flipped_vertical
        )
class PuzzleModel:
    """Stores and manages the state of the puzzle."""

    def __init__(self, grid_size=3):
        self.grid_size = grid_size
        self.tiles = []

        self.moves = 0
        self.hints_used = 0
        self.solved = False

    def create_tiles(self):
        """Create empty tile objects for the selected grid size."""
        self.tiles = []

        total_tiles = self.grid_size * self.grid_size

        for position in range(total_tiles):
            tile = Tile(position, position)
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
    print("Incorrect tiles:", puzzle.count_incorrect_tiles())

    try:
        image = ImageProcessor.load_image("test.jpg")
        image = ImageProcessor.resize_image(image)

        print("Image loaded successfully.")
        print("Image size:", image.shape)

    except (FileNotFoundError, ValueError) as error:
        print("Image error:", error)