import cv2
import numpy as np
import random
import tkinter as tk 

from pathlib import Path
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk 

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

    def get_transformation_count(self):
        """Return the number of transformations for the selected grid."""

        transformation_counts = {
            3: 6,
            4: 12,
            5: 20
        }

        return transformation_counts[self.grid_size]
    
    def generate_random_transformations(self):
        """Generate a complete list of random puzzle transformations."""

        if not self.tiles:
            raise ValueError("Cannot scramble a puzzle with no tiles.")

        total_tiles = len(self.tiles)
        transformation_count = self.get_transformation_count()

        transformations = []

        # Guarantee that all three required transformation types are used.
        first_position, second_position = random.sample(
            range(total_tiles),
            2
        )

        transformations.append(
            SwapTransformation(
                first_position,
                second_position
            )
        )

        transformations.append(
            RotateTransformation(
                random.randrange(total_tiles),
                random.choice((90, 180, 270))
            )
        )

        transformations.append(
            FlipTransformation(
                random.randrange(total_tiles),
                random.choice(("horizontal", "vertical"))
            )
        )

        # Generate the remaining transformations randomly.
        while len(transformations) < transformation_count:

            transformation_type = random.choice(
                ("swap", "rotate", "flip")
            )

            if transformation_type == "swap":
                first_position, second_position = random.sample(
                    range(total_tiles),
                    2
                )

                transformation = SwapTransformation(
                    first_position,
                    second_position
                )

            elif transformation_type == "rotate":
                transformation = RotateTransformation(
                    random.randrange(total_tiles),
                    random.choice((90, 180, 270))
                )

            else:
                transformation = FlipTransformation(
                    random.randrange(total_tiles),
                    random.choice(("horizontal", "vertical"))
                )

            transformations.append(transformation)

        random.shuffle(transformations)

        return transformations
    
    def scramble(self):
        """Generate and apply random transformations to the puzzle."""

        transformations = self.generate_random_transformations()

        for transformation in transformations:
            transformation.apply(self)

        # Automatic scrambling does not count as player moves.
        self.moves = 0
        self.hints_used = 0
        self.solved = False

        return transformations

    def swap_tiles(self, first_position, second_position):
        """Swap two puzzle tiles and count one player move."""

        total_tiles = len(self.tiles)

        if not (
            0 <= first_position < total_tiles
            and 0 <= second_position < total_tiles
        ):
            raise ValueError("Tile position is outside the puzzle.")

        if first_position == second_position:
            return False

        transformation = SwapTransformation(
            first_position,
            second_position
        )

        transformation.apply(self)

        self.moves += 1

        return True

    def rotate_tile(self, position, angle=90):
        """Rotate one puzzle tile and count one player move."""

        if not 0 <= position < len(self.tiles):
            raise ValueError("Tile position is outside the puzzle.")

        transformation = RotateTransformation(
            position,
            angle
        )

        transformation.apply(self)

        self.moves += 1

    def flip_tile(self, position, direction="horizontal"):
        """Flip one puzzle tile and count one player move."""

        if not 0 <= position < len(self.tiles):
            raise ValueError("Tile position is outside the puzzle.")

        transformation = FlipTransformation(
            position,
            direction
        )

        transformation.apply(self)

        self.moves += 1

    def reassemble_image(self):
        """Reassemble the current puzzle tiles into one complete image."""

        expected_tiles = self.grid_size * self.grid_size

        if len(self.tiles) != expected_tiles:
            raise ValueError(
                "The number of tiles does not match the selected grid size."
            )

        tile_images = []

        for tile in self.tiles:
            image = tile.get_image()

            if image is None:
                raise ValueError(
                    "Cannot reassemble the puzzle because a tile has no image."
                )

            tile_images.append(image)

        # Make sure all tile images have identical dimensions.
        first_shape = tile_images[0].shape

        for image in tile_images:
            if image.shape != first_shape:
                raise ValueError(
                    "All puzzle tiles must have the same dimensions."
                )

        rows = []

        for row_index in range(self.grid_size):
            start = row_index * self.grid_size
            end = start + self.grid_size

            row_images = tile_images[start:end]

            combined_row = np.hstack(row_images)
            rows.append(combined_row)

        complete_image = np.vstack(rows)

        return complete_image
    def solve(self):
        """Restore every tile to its correct position and orientation."""

        if not self.tiles:
            raise ValueError("Cannot solve a puzzle with no tiles.")

        self.tiles.sort(
            key=lambda tile: tile.correct_position
        )

        for tile in self.tiles:
            tile.reset_orientation()

        self.moves = 0
        self.solved = True
    
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

class PuzzleApp:
    """Tkinter interface for the image puzzle game."""

    def __init__(self, root):
        self.root = root
        self.root.title("Image Puzzle Game")

        self.puzzle = None
        self.original_image = None
        self.scrambled_image = None

        self.selected_position = None

        self.original_photo = None
        self.scrambled_photo = None

        self.grid_size = tk.IntVar(value=3)
        self.moves_var = tk.StringVar(value="Moves: 0")
        self.incorrect_var = tk.StringVar(value="Incorrect Tiles: 0")
        self.hints_var = tk.StringVar(value="Hints Remaining: 3")

        self.create_widgets()

    def create_widgets(self):
        """Create the main interface widgets."""

        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        tk.Label(
            control_frame,
            text="Grid Size:"
        ).pack(side=tk.LEFT, padx=5)

        for size in (3, 4, 5):
            tk.Radiobutton(
                control_frame,
                text=f"{size} x {size}",
                variable=self.grid_size,
                value=size
            ).pack(side=tk.LEFT)

        self.load_button = tk.Button(
            control_frame,
            text="Load Image",
            command=self.load_image
        )

        self.load_button.pack(
            side=tk.LEFT,
            padx=10
        )
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=5)

        tk.Label(
            status_frame,
            textvariable=self.moves_var
        ).pack(side=tk.LEFT, padx=10)

        tk.Label(
            status_frame,
            textvariable=self.incorrect_var
        ).pack(side=tk.LEFT, padx=10)

        tk.Label(
           status_frame,
           textvariable=self.hints_var
        ).pack(side=tk.LEFT, padx=10)

        self.hint_button = tk.Button(
            status_frame,
            text="Hint",
            command=self.show_hint,
            state=tk.DISABLED
        )
        self.hint_button.pack(side=tk.LEFT, padx=5)

        self.solve_button = tk.Button(
            status_frame,
            text="Solve",
            command=self.solve_puzzle,
            state=tk.DISABLED
        )
        self.solve_button.pack(side=tk.LEFT, padx=5)

        image_frame = tk.Frame(self.root)
        image_frame.pack(padx=10, pady=10)

        original_frame = tk.Frame(image_frame)
        original_frame.pack(
            side=tk.LEFT,
            padx=10
        )

        tk.Label(
            original_frame,
            text="Original Image"
        ).pack()

        self.original_label = tk.Label(
            original_frame,
            text="No image loaded",
            width=45,
            height=20,
            relief="solid"
        )

        self.original_label.pack()

        puzzle_frame = tk.Frame(image_frame)
        puzzle_frame.pack(
            side=tk.LEFT,
            padx=10
        )

        tk.Label(
            puzzle_frame,
            text="Puzzle"
        ).pack()

        self.puzzle_label = tk.Label(
            puzzle_frame,
            text="No image loaded",
            width=45,
            height=20,
            relief="solid"
        )

        self.puzzle_label.pack()

        self.puzzle_label.bind(
            "<Button-1>",
            self.on_puzzle_left_click
        )
        self.puzzle_label.bind(
            "<Button-3>",
            self.on_puzzle_right_click
        )
        self.puzzle_label.bind(
            "<Shift-Button-1>",
            self.on_puzzle_shift_left_click
        )

    def convert_for_tkinter(self, image):
        """Convert an OpenCV image into a Tkinter-compatible image."""

        image_rgb = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        pil_image = Image.fromarray(image_rgb)

        return ImageTk.PhotoImage(pil_image)
    
    def load_image(self):
        """Allow the player to select and load an image."""

        file_path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("BMP files", "*.bmp")
            ]
        )

        if not file_path:
            return
    
        try:
            image = ImageProcessor.load_image(file_path)
            image = ImageProcessor.resize_image(image)

            prepared_image = ImageProcessor.prepare_for_grid(
                image,
                self.grid_size.get()
            )

            image_tiles = ImageProcessor.split_into_tiles(
                prepared_image,
                self.grid_size.get()
            )

            new_puzzle = PuzzleModel(
                self.grid_size.get()
            )

            new_puzzle.create_tiles(image_tiles)
            new_puzzle.scramble()

            scrambled_image = new_puzzle.reassemble_image()

        except (FileNotFoundError, ValueError) as error:
            messagebox.showerror(
                "Image Error",
                str(error)
            )
            return

        # Only update the application after everything succeeds.
        self.puzzle = new_puzzle
        self.original_image = prepared_image
        self.scrambled_image = scrambled_image
        self.selected_position = None

        self.display_images()
        self.update_status()

        self.hint_button.config(state=tk.NORMAL)
        self.solve_button.config(state=tk.NORMAL)

    def display_images(self):
        """Display the original and scrambled images."""

        self.original_photo = self.convert_for_tkinter(
            self.original_image
        )

        puzzle_display = self.create_puzzle_display_image()

        self.scrambled_photo = self.convert_for_tkinter(
            puzzle_display
)

        self.original_label.config(
            image=self.original_photo,
            text="",
            width=0,
            height=0
        )

        self.puzzle_label.config(
            image=self.scrambled_photo,
            text="",
            width=0,
            height=0
        )

    def create_puzzle_display_image(self):
        """Create a puzzle image with grid lines and status markings."""

        if self.scrambled_image is None:
            return None

        display_image = self.scrambled_image.copy()

        if self.puzzle is None:
            return display_image

        grid_size = self.puzzle.grid_size
        height, width = display_image.shape[:2]

        tile_height = height // grid_size
        tile_width = width // grid_size

        # Draw faint grid lines.
        for index in range(1, grid_size):
            x = index * tile_width

            cv2.line(
                display_image,
                (x, 0),
                (x, height),
                (180, 180, 180),
                1
            )

            y = index * tile_height

            cv2.line(
                display_image,
                (0, y),
                (width, y),
                (180, 180, 180),
                1
            )

        # Draw green ticks on correctly placed and oriented tiles.
        for position, tile in enumerate(self.puzzle.tiles):

            if not tile.is_correct(position):
                continue

            row = position // grid_size
            column = position % grid_size

            x1 = column * tile_width
            y1 = row * tile_height

            tick_start = (
                x1 + int(tile_width * 0.68),
                y1 + int(tile_height * 0.22)
            )

            tick_middle = (
                x1 + int(tile_width * 0.76),
                y1 + int(tile_height * 0.32)
            )

            tick_end = (
                x1 + int(tile_width * 0.90),
                y1 + int(tile_height * 0.12)
            )

            cv2.line(
                display_image,
                tick_start,
                tick_middle,
                (0, 255, 0),
                3
            )

            cv2.line(
                display_image,
                tick_middle,
                tick_end,
                (0, 255, 0),
                3
            )

        # Draw a red border around the selected tile.
        if self.selected_position is not None:

            row = self.selected_position // grid_size
            column = self.selected_position % grid_size

            x1 = column * tile_width
            y1 = row * tile_height

            x2 = x1 + tile_width - 1
            y2 = y1 + tile_height - 1

            cv2.rectangle(
                display_image,
                (x1 + 2, y1 + 2),
                (x2 - 2, y2 - 2),
                (0, 0, 255),
                3
            )

        return display_image
    def update_status(self):
        """Update moves, incorrect tiles, and hints remaining."""

        if self.puzzle is None:
           self.moves_var.set("Moves: 0")
           self.incorrect_var.set("Incorrect Tiles: 0")
           self.hints_var.set("Hints Remaining: 3")
           return

        incorrect = self.puzzle.count_incorrect_tiles()
        hints_remaining = 3 - self.puzzle.hints_used

        self.moves_var.set(
            f"Moves: {self.puzzle.moves}"
        )

        self.incorrect_var.set(
            f"Incorrect Tiles: {incorrect}"
        )

        self.hints_var.set(
            f"Hints Remaining: {hints_remaining}"
        )

    def check_for_completion(self):
        """Check whether the player has completed the puzzle."""

        if self.puzzle is None:
            return

        if not self.puzzle.check_solved():
            return

        self.selected_position = None

        self.scrambled_image = self.puzzle.reassemble_image()

        self.display_images()
        self.update_status()

        self.hint_button.config(state=tk.DISABLED)
        self.solve_button.config(state=tk.DISABLED)

        messagebox.showinfo(
            "Puzzle Complete",
            f"Congratulations! You solved the puzzle in "
            f"{self.puzzle.moves} moves."
        )

    def get_clicked_position(self, event):
        """Return the puzzle position clicked by the player."""

        if self.puzzle is None or self.scrambled_image is None:
            return None

        height, width = self.scrambled_image.shape[:2]
        grid_size = self.puzzle.grid_size

        # Ignore clicks outside the actual image.
        if event.x < 0 or event.y < 0:
            return None

        if event.x >= width or event.y >= height:
            return None

        tile_width = width // grid_size
        tile_height = height // grid_size

        column = event.x // tile_width
        row = event.y // tile_height

        position = row * grid_size + column

        if position < 0 or position >= len(self.puzzle.tiles):
            return None

        return position

    def on_puzzle_left_click(self, event):
        """Select, deselect, or swap puzzle tiles."""

        if self.puzzle is None:
            return

        if self.puzzle.solved:
            return

        # Shift + left-click is handled separately.
        if event.state & 0x0001:
            return

        position = self.get_clicked_position(event)

        if position is None:
            return

        # First click selects a tile.
        if self.selected_position is None:
            self.selected_position = position

            self.display_images()

            print(
               "Selected tile:",
                self.selected_position
            )
            

            return

        # Clicking the selected tile again deselects it.
        if position == self.selected_position:
            self.selected_position = None

            self.display_images()

            print("Tile deselected")

            return

        # Clicking a different tile swaps the two.
        first_position = self.selected_position

        try:
            self.puzzle.swap_tiles(
                first_position,
                position
            )

            self.scrambled_image = (
                self.puzzle.reassemble_image()
            )

        except ValueError as error:
            messagebox.showerror(
                "Puzzle Error",
                str(error)
            )

            self.selected_position = None
            return

        self.selected_position = None

        self.display_images()
        self.update_status()
        self.check_for_completion()

        print(
            "Swapped tiles:",
            first_position,
            "and",
            position
        )

    def on_puzzle_right_click(self, event):
        """Rotate the clicked tile 90 degrees clockwise."""

        if self.puzzle is None:
            return

        if self.puzzle.solved:
            return

        position = self.get_clicked_position(event)

        if position is None:
            return

        # Any selected tile is deselected.
        self.selected_position = None

        try:
            self.puzzle.rotate_tile(
                position,
                90
            )

            self.scrambled_image = (
            self.puzzle.reassemble_image()
            )

        except ValueError as error:
            messagebox.showerror(
                "Puzzle Error",
                str(error)
            )
            return

        self.display_images()
        self.update_status()
        self.check_for_completion()

        print(
            "Rotated tile:",
            position
        )
    def on_puzzle_shift_left_click(self, event):
        """Flip the clicked tile horizontally."""

        if self.puzzle is None:
            return

        if self.puzzle.solved:
            return

        position = self.get_clicked_position(event)

        if position is None:
            return

        # Deselect any currently selected tile.
        self.selected_position = None

        try:
            self.puzzle.flip_tile(
                position,
                "horizontal"
            )

            self.scrambled_image = (
                self.puzzle.reassemble_image()
            )

        except ValueError as error:
            messagebox.showerror(
                "Puzzle Error",
                str(error)
            )
            return

        self.display_images()
        self.update_status()
        self.check_for_completion()

        print(
            "Horizontally flipped tile:",
            position
        )

    def draw_hint_circle(self, image, position):
        """Draw a blue circle at the centre of a puzzle tile."""

        grid_size = self.puzzle.grid_size

        height, width = image.shape[:2]

        tile_height = height // grid_size
        tile_width = width // grid_size

        row = position // grid_size
        column = position % grid_size

        centre_x = column * tile_width + tile_width // 2
        centre_y = row * tile_height + tile_height // 2

        radius = max(
           8,
           min(tile_width, tile_height) // 6
        )

        cv2.circle(
            image,
            (centre_x, centre_y),
            radius,
            (255, 0, 0),
            3
        )
          
    def show_hint(self):
        """Show the location and correct home of one incorrect tile."""

        if self.puzzle is None:
           return

        if self.puzzle.hints_used >= 3:
            self.hint_button.config(state=tk.DISABLED)
            return

        incorrect_positions = []

        for position, tile in enumerate(self.puzzle.tiles):
            if not tile.is_correct(position):
                incorrect_positions.append(position)

        if not incorrect_positions:
            messagebox.showinfo(
                "Hint",
                "The puzzle is already solved."
            )
            return

        current_position = random.choice(
            incorrect_positions
        )

        tile = self.puzzle.tiles[current_position]
        correct_position = tile.correct_position

        original_hint = self.original_image.copy()
        puzzle_hint = self.scrambled_image.copy()

        self.draw_hint_circle(
            puzzle_hint,
            current_position
        )

        self.draw_hint_circle(
            original_hint,
            correct_position
        )

        self.original_photo = self.convert_for_tkinter(
            original_hint
        )

        self.scrambled_photo = self.convert_for_tkinter(
            puzzle_hint
        )

        self.original_label.config(
            image=self.original_photo
        )

        self.puzzle_label.config(
            image=self.scrambled_photo
        )

        self.puzzle.hints_used += 1

        self.update_status()

        if self.puzzle.hints_used >= 3:
            self.hint_button.config(
                state=tk.DISABLED
           )
    def solve_puzzle(self):
        """Instantly restore the puzzle."""

        if self.puzzle is None:
            return

        try:
            self.puzzle.solve()

            self.scrambled_image = (
                self.puzzle.reassemble_image()
            )

        except ValueError as error:
            messagebox.showerror(
                "Puzzle Error",
                str(error)
            )
            return

        self.display_images()
        self.update_status()

        self.hint_button.config(state=tk.DISABLED)
        self.solve_button.config(state=tk.DISABLED)

        messagebox.showinfo(
            "Puzzle Solved",
            "The puzzle has been solved."
        )

if __name__ == "__main__":
    root = tk.Tk()

    app = PuzzleApp(root)

    root.mainloop()

