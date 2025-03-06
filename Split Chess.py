import pygame
import os
from enum import Enum, auto

# Constants
BOARD_SIZE = 720  # Size of the chessboard
SIDEBAR_WIDTH = BOARD_SIZE / 3.2  # Width of the sidebar
WIDTH, HEIGHT = BOARD_SIZE + SIDEBAR_WIDTH, BOARD_SIZE
ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_SIZE // COLS

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)
HIGHLIGHT_COLOR = (100, 200, 100)
SIDEBAR_COLOR = (50, 50, 50)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_TEXT_COLOR = (255, 200, 0)
WIN_TEXT_COLOR = (0, 255, 0)
BUTTON_COLOR = (100, 100, 100)
BUTTON_HOVER_COLOR = (150, 150, 150)

# Piece types
class PieceType(Enum):
    PAWN = auto()
    KNIGHT = auto()
    BISHOP = auto()
    ROOK = auto()
    QUEEN = auto()
    KING = auto()

# Piece colors
class PieceColor(Enum):
    WHITE = "w"
    BLACK = "b"

def load_images():
    pieces = {}
    base_path = os.path.join(os.path.dirname(__file__), 'images')  # Get the images folder relative to the script

    for color in PieceColor:
        for piece in PieceType:
            # Load full piece image
            path = os.path.join(base_path, f'{color.value}_{piece.name.lower()}.png')
            image = pygame.image.load(path)
            pieces[f'{color.value}_{piece.name.lower()}'] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))

            # Skip loading split images for kings
            if piece != PieceType.KING:
                for fraction in ['half', 'quarter', 'eighth']:
                    path = os.path.join(base_path, f'{color.value}_{piece.name.lower()}_{fraction}.png')
                    image = pygame.image.load(path)
                    pieces[f'{color.value}_{piece.name.lower()}_{fraction}'] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
                    
    return pieces

piece_images = load_images()

# Chessboard class
class ChessBoard:
    def __init__(self, screen):
        self.reset()
        self.screen = screen
        self.flipped = False

    def reset(self):
        # Reset the game state to the initial setup.
        self.board = [
            ["b_rook", "b_knight", "b_bishop", "b_queen", "b_king", "b_bishop", "b_knight", "b_rook"],
            ["b_pawn"] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,
            ["w_pawn"] * 8,
            ["w_rook", "w_knight", "w_bishop", "w_queen", "w_king", "w_bishop", "w_knight", "w_rook"]
        ]
        self.turn = PieceColor.WHITE
        self.selected_piece = None
        self.selected_pos = None
        self.valid_moves = []
        self.potential_moves = []  # Track potential moves before committing
        self.en_passant_target = None
        self.castling_rights = {PieceColor.WHITE: {"king_side": True, "queen_side": True},
                                PieceColor.BLACK: {"king_side": True, "queen_side": True}}
        self.game_over = False  # Track if the game is over
        self.winner = None  # Track the winner
        self.captured_pieces = {}  # Track captured pieces during potential moves

    def get_valid_moves(self, piece, x, y):
        moves_list = []
        piece_type = piece.split('_')[1]
        directions = {
            "bishop": [(1, 1), (1, -1), (-1, 1), (-1, -1)],
            "rook": [(1, 0), (-1, 0), (0, 1), (0, -1)],
            "queen": [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)],
            "king": [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]
        }
        if piece_type == "pawn":
            direction = -1 if piece.startswith("w") else 1
            start_row = 6 if piece.startswith("w") else 1
            if 0 <= y + direction < ROWS and self.board[y + direction][x] is None:
                moves_list.append((x, y + direction))
                if y == start_row and self.board[y + 2 * direction][x] is None:
                    moves_list.append((x, y + 2 * direction))
            for dx in [-1, 1]:
                nx, ny = x + dx, y + direction
                if 0 <= nx < COLS and 0 <= ny < ROWS:
                    if self.board[ny][nx] and self.board[ny][nx][0] != piece[0]:  # Normal capture
                        moves_list.append((nx, ny))
                    elif (nx, ny) == self.en_passant_target:  # En passant capture
                        moves_list.append((nx, ny))
        elif piece_type == "knight":
            for dx, dy in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < COLS and 0 <= ny < ROWS and (self.board[ny][nx] is None or self.board[ny][nx][0] != piece[0]):
                    moves_list.append((nx, ny))
        elif piece_type == "king":
            for dx, dy in directions["king"]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < COLS and 0 <= ny < ROWS and (self.board[ny][nx] is None or self.board[ny][nx][0] != piece[0]):
                    moves_list.append((nx, ny))
            # Castling
            if self.castling_rights[PieceColor(piece[0])]["king_side"]:
                if self.board[y][x + 1] is None and self.board[y][x + 2] is None:
                    moves_list.append((x + 2, y))
            if self.castling_rights[PieceColor(piece[0])]["queen_side"]:
                if self.board[y][x - 1] is None and self.board[y][x - 2] is None and self.board[y][x - 3] is None:
                    moves_list.append((x - 2, y))
        else:
            for dx, dy in directions.get(piece_type, []):
                nx, ny = x + dx, y + dy
                while 0 <= nx < COLS and 0 <= ny < ROWS:
                    if self.board[ny][nx] is None:
                        moves_list.append((nx, ny))
                    elif self.board[ny][nx][0] != piece[0]:
                        moves_list.append((nx, ny))
                        break
                    else:
                        break
                    nx += dx
                    ny += dy

        return moves_list

    def handle_click(self, pos):
        # Check if the game is over
        if self.game_over:
            # Only allow clicks on the restart button
            if BOARD_SIZE < pos[0] < WIDTH and HEIGHT // 2 + 50 < pos[1] < HEIGHT // 2 + 100:
                self.reset()  # Restart the game
            return  # Ignore all other clicks

        # Handle sidebar clicks
        if pos[0] >= BOARD_SIZE:
            # Check if the pass button is clicked
            if BOARD_SIZE < pos[0] < WIDTH and HEIGHT // 2 - 25 < pos[1] < HEIGHT // 2 + 25:
                self.commit_move()  # Commit the move and split the piece
            return

        # Handle chessboard clicks
        col = pos[0] // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE

        # Adjust row and column if the board is flipped
        if self.flipped:
            col = COLS - 1 - col
            row = ROWS - 1 - row

        if self.selected_piece:
            # Check if the player clicks on the same piece again to deselect it
            if (col, row) == self.selected_pos and len(self.potential_moves) == 0:
                # Deselect the piece only if no moves have been made
                self.selected_piece = None
                self.selected_pos = None
                self.valid_moves = []
                self.potential_moves = []
                return

            # Check if the player clicks on a selected move option to deselect it
            if (col, row) in self.potential_moves:
                # Remove the move from potential moves
                self.potential_moves.remove((col, row))

                # Restore the captured piece (if any) on the deselected square
                if (col, row) in self.captured_pieces:
                    self.board[row][col] = self.captured_pieces[(col, row)]

                # Remove the ghost piece from the deselected square
                else:
                    self.board[row][col] = None

                # If there's still one move left, revert it to a full ghost piece
                if len(self.potential_moves) == 1:
                    col2, row2 = self.potential_moves[0]
                    self.board[row2][col2] = self.selected_piece  # Revert to full piece
                return

            if (col, row) in self.valid_moves:
                # Prevent kings from performing quantum moves
                if self.selected_piece.split('_')[1] == "king" and len(self.potential_moves) >= 1:
                    return  # Kings can only have one move

                # Prevent eighth pieces from splitting
                if self.selected_piece.endswith("_eighth") and len(self.potential_moves) >= 1:
                    return  # Eighth pieces cannot split
                
                elif (len(self.potential_moves) >= 2):
                    return  # Half and quarter pieces can only split into two moves

                # Track the captured piece (if any) on the target square
                if self.board[row][col] is not None:
                    self.captured_pieces[(col, row)] = self.board[row][col]

                # Add the move to potential moves
                self.potential_moves.append((col, row))

                # Update ghost pieces
                if len(self.potential_moves) == 1:
                    # Display a full ghost piece
                    self.board[row][col] = self.selected_piece
                elif len(self.potential_moves) == 2:
                    # Split the ghost piece into smaller pieces
                    col1, row1 = self.potential_moves[0]
                    col2, row2 = self.potential_moves[1]
                    if not self.selected_piece.endswith("_half") and not self.selected_piece.endswith("_quarter"):
                        # If the selected piece is a full piece, split it into half pieces
                        self.board[row1][col1] = f"{self.selected_piece.split('_')[0]}_{self.selected_piece.split('_')[1]}_half"
                        self.board[row2][col2] = f"{self.selected_piece.split('_')[0]}_{self.selected_piece.split('_')[1]}_half"
                    elif self.selected_piece.endswith("_half"):
                        # If the selected piece is a half piece, split it into quarter pieces
                        self.board[row1][col1] = f"{self.selected_piece.split('_')[0]}_{self.selected_piece.split('_')[1]}_quarter"
                        self.board[row2][col2] = f"{self.selected_piece.split('_')[0]}_{self.selected_piece.split('_')[1]}_quarter"
                    elif self.selected_piece.endswith("_quarter"):
                        # If the selected piece is a quarter piece, split it into eighth pieces
                        self.board[row1][col1] = f"{self.selected_piece.split('_')[0]}_{self.selected_piece.split('_')[1]}_eighth"
                        self.board[row2][col2] = f"{self.selected_piece.split('_')[0]}_{self.selected_piece.split('_')[1]}_eighth"
        else:
            if self.board[row][col] and self.board[row][col][0] == self.turn.value:
                self.selected_piece = self.board[row][col]
                self.selected_pos = (col, row)
                self.valid_moves = self.get_valid_moves(self.selected_piece, col, row)
                self.potential_moves = []  # Reset potential moves when a new piece is selected
            
    def commit_move(self):
        if self.selected_piece and self.potential_moves:
            # Handle en passant capture
            for move in self.potential_moves:
                col, row = move
                if (col, row) == self.en_passant_target:
                    # Remove the pawn that was captured en passant
                    captured_pawn_row = row + 1 if self.turn == PieceColor.WHITE else row - 1
                    self.board[captured_pawn_row][col] = None

            # Handle castling
            if self.selected_piece.split('_')[1] == "king":
                original_col, original_row = self.selected_pos
                for move in self.potential_moves:
                    col, row = move
                    if abs(col - original_col) == 2:  # Castling move
                        if col > original_col:  # King-side castling
                            # Move the rook
                            self.board[row][col - 1] = self.board[row][7]
                            self.board[row][7] = None
                        else:  # Queen-side castling
                            # Move the rook
                            self.board[row][col + 1] = self.board[row][0]
                            self.board[row][0] = None
                        # Disable castling rights for this color
                        self.castling_rights[self.turn]["king_side"] = False
                        self.castling_rights[self.turn]["queen_side"] = False

            # Split the piece into smaller pieces
            for i, move in enumerate(self.potential_moves):
                col, row = move
                if self.board[row][col] is None:
                    # Place the smaller piece
                    if self.selected_piece.endswith("_half"):
                        self.board[row][col] = f"{self.selected_piece.split('_')[0]}_{self.selected_piece.split('_')[1]}_quarter"
                    elif self.selected_piece.endswith("_quarter"):
                        self.board[row][col] = f"{self.selected_piece.split('_')[0]}_{self.selected_piece.split('_')[1]}_eighth"
                    else:
                        self.board[row][col] = self.selected_piece
                else:
                    # Handle capture (if needed)
                    pass

            # Remove the original piece
            original_col, original_row = self.selected_pos
            self.board[original_row][original_col] = None

            # Disable castling rights if the king or rooks move
            if self.selected_piece.split('_')[1] == "king":
                self.castling_rights[self.turn]["king_side"] = False
                self.castling_rights[self.turn]["queen_side"] = False
            elif self.selected_piece.split('_')[1] == "rook":
                if original_col == 0:  # Queen-side rook
                    self.castling_rights[self.turn]["queen_side"] = False
                elif original_col == 7:  # King-side rook
                    self.castling_rights[self.turn]["king_side"] = False

            # Check for pawn promotion
            for move in self.potential_moves:
                col, row = move
                piece = self.board[row][col]
                if piece and piece.split('_')[1] == "pawn":
                    if (self.turn == PieceColor.WHITE and row == 0) or (self.turn == PieceColor.BLACK and row == 7):
                        # Determine the suffix of the pawn (full, half, quarter, or eighth)
                        suffix = ""
                        if piece.endswith("_half"):
                            suffix = "_half"
                        elif piece.endswith("_quarter"):
                            suffix = "_quarter"
                        elif piece.endswith("_eighth"):
                            suffix = "_eighth"
                        
                        # Promote the pawn to a queen of the same proportion
                        self.board[row][col] = f"{self.turn.value}_queen{suffix}"

            # Set en passant target square if a pawn moves two squares forward
            if self.selected_piece.split('_')[1] == "pawn":
                start_row = 6 if self.turn == PieceColor.WHITE else 1
                if abs(self.selected_pos[1] - self.potential_moves[0][1]) == 2:
                    self.en_passant_target = (self.selected_pos[0], (self.selected_pos[1] + self.potential_moves[0][1]) // 2)
                else:
                    self.en_passant_target = None
            else:
                self.en_passant_target = None

            # Reset the selected piece, potential moves, and captured pieces
            self.selected_piece = None
            self.selected_pos = None
            self.valid_moves = []
            self.potential_moves = []
            self.captured_pieces = {}

            # Check if either player has lost their king
            white_king_found = False
            black_king_found = False
            for row in self.board:
                for piece in row:
                    if piece and piece.split('_')[1] == "king":
                        if piece.startswith("w"):
                            white_king_found = True
                        elif piece.startswith("b"):
                            black_king_found = True

            if not white_king_found:
                self.game_over = True
                self.winner = PieceColor.BLACK
            elif not black_king_found:
                self.game_over = True
                self.winner = PieceColor.WHITE

            # Switch turns
            self.turn = PieceColor.BLACK if self.turn == PieceColor.WHITE else PieceColor.WHITE

    def draw_board(self):
        for row in range(ROWS):
            for col in range(COLS):
                # Adjust row and column if the board is flipped
                adjusted_row = ROWS - 1 - row if self.flipped else row
                adjusted_col = COLS - 1 - col if self.flipped else col

                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                if (col, row) in self.valid_moves:
                    color = HIGHLIGHT_COLOR
                pygame.draw.rect(self.screen, color, (adjusted_col * SQUARE_SIZE, adjusted_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Highlight the original position of the selected piece
        if self.selected_piece and self.selected_pos:
            col, row = self.selected_pos
            adjusted_col = COLS - 1 - col if self.flipped else col
            adjusted_row = ROWS - 1 - row if self.flipped else row
            pygame.draw.rect(self.screen, (255, 255, 0), (adjusted_col * SQUARE_SIZE, adjusted_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)

    def draw_pieces(self):
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece:
                    # Adjust row and column if the board is flipped
                    adjusted_row = ROWS - 1 - row if self.flipped else row
                    adjusted_col = COLS - 1 - col if self.flipped else col
                    self.screen.blit(piece_images[piece], (adjusted_col * SQUARE_SIZE, adjusted_row * SQUARE_SIZE))
    
    def draw_sidebar(self):
        # Draw sidebar background
        pygame.draw.rect(self.screen, SIDEBAR_COLOR, (BOARD_SIZE, 0, SIDEBAR_WIDTH, HEIGHT))

        # Set up font
        font = pygame.font.Font(None, 36)

        # Calculate vertical spacing
        sidebar_center_x = BOARD_SIZE + SIDEBAR_WIDTH // 2
        vertical_spacing = HEIGHT // 8

        # Determine which player is at the top based on the flipped state
        top_player = "White" if self.flipped else "Black"
        bottom_player = "Black" if self.flipped else "White"

        # Determine which player's turn it is based on the flipped state
        top_turn = PieceColor.WHITE if self.flipped else PieceColor.BLACK
        bottom_turn = PieceColor.BLACK if self.flipped else PieceColor.WHITE

        # Draw the top player label
        top_text = font.render(top_player, True, HIGHLIGHT_TEXT_COLOR if self.turn == top_turn else TEXT_COLOR)
        top_rect = top_text.get_rect(center=(sidebar_center_x, vertical_spacing))
        self.screen.blit(top_text, top_rect)

        # Draw the bottom player label
        bottom_text = font.render(bottom_player, True, HIGHLIGHT_TEXT_COLOR if self.turn == bottom_turn else TEXT_COLOR)
        bottom_rect = bottom_text.get_rect(center=(sidebar_center_x, HEIGHT - vertical_spacing))
        self.screen.blit(bottom_text, bottom_rect)

        # Draw pass button
        pass_button = pygame.Rect(BOARD_SIZE + 20, HEIGHT // 2 - 25, SIDEBAR_WIDTH - 40, 50)
        mouse_pos = pygame.mouse.get_pos()
        button_color = BUTTON_HOVER_COLOR if pass_button.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(self.screen, button_color, pass_button)
        pass_text = font.render("Pass", True, TEXT_COLOR)
        pass_text_rect = pass_text.get_rect(center=pass_button.center)
        self.screen.blit(pass_text, pass_text_rect)

        if self.game_over:
            # Draw winner text
            winner_text = font.render(f"{self.winner.name} Wins!", True, WIN_TEXT_COLOR)
            winner_rect = winner_text.get_rect(center=(sidebar_center_x, HEIGHT // 2 - 75))
            self.screen.blit(winner_text, winner_rect)

            # Draw restart button
            restart_button = pygame.Rect(BOARD_SIZE + 20, HEIGHT // 2 + 50, SIDEBAR_WIDTH - 40, 50)
            button_color = BUTTON_HOVER_COLOR if restart_button.collidepoint(mouse_pos) else BUTTON_COLOR
            pygame.draw.rect(self.screen, button_color, restart_button)
            restart_text = font.render("Restart", True, TEXT_COLOR)
            restart_text_rect = restart_text.get_rect(center=restart_button.center)
            self.screen.blit(restart_text, restart_text_rect)

# Main loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess")
    clock = pygame.time.Clock()
    chess_board = ChessBoard(screen)

    running = True
    while running:
        screen.fill(WHITE)
        chess_board.draw_board()
        chess_board.draw_pieces()
        chess_board.draw_sidebar()
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                chess_board.handle_click(pygame.mouse.get_pos())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:  # Toggle board flip on 'F' key press
                    chess_board.flipped = not chess_board.flipped

        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()