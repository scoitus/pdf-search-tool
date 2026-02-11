"""
Boolean query parser for PDF search.

Supports queries like:
    climate AND policy
    climate OR weather
    "exact phrase" AND summary
    climate AND (policy OR regulation)
    climate AND NOT draft

Operator precedence: NOT > AND > OR
Quoted strings are treated as literal phrases.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    TERM = auto()
    PHRASE = auto()     # Quoted string
    AND = auto()
    OR = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()


@dataclass
class Token:
    type: TokenType
    value: str


# --- AST Nodes ---

class ASTNode:
    pass


@dataclass
class TermNode(ASTNode):
    """A single search term."""
    term: str


@dataclass
class PhraseNode(ASTNode):
    """An exact quoted phrase."""
    phrase: str


@dataclass
class AndNode(ASTNode):
    """Both children must match."""
    left: ASTNode
    right: ASTNode


@dataclass
class OrNode(ASTNode):
    """Either child can match."""
    left: ASTNode
    right: ASTNode


@dataclass
class NotNode(ASTNode):
    """Child must NOT match (used with AND: A AND NOT B)."""
    child: ASTNode


class ParseError(Exception):
    pass


class BooleanParser:
    """Tokenizes, parses, and evaluates boolean search queries."""

    def tokenize(self, query: str) -> list[Token]:
        """Split query into tokens."""
        tokens = []
        i = 0
        while i < len(query):
            # Skip whitespace
            if query[i].isspace():
                i += 1
                continue

            # Quoted phrase
            if query[i] == '"':
                end = query.find('"', i + 1)
                if end == -1:
                    # Unterminated quote — treat rest as phrase
                    tokens.append(Token(TokenType.PHRASE, query[i + 1:]))
                    break
                tokens.append(Token(TokenType.PHRASE, query[i + 1:end]))
                i = end + 1
                continue

            # Parentheses
            if query[i] == '(':
                tokens.append(Token(TokenType.LPAREN, '('))
                i += 1
                continue
            if query[i] == ')':
                tokens.append(Token(TokenType.RPAREN, ')'))
                i += 1
                continue

            # Read a word
            j = i
            while j < len(query) and not query[j].isspace() and query[j] not in '()"':
                j += 1
            word = query[i:j]
            upper = word.upper()

            if upper == "AND":
                tokens.append(Token(TokenType.AND, "AND"))
            elif upper == "OR":
                tokens.append(Token(TokenType.OR, "OR"))
            elif upper == "NOT":
                tokens.append(Token(TokenType.NOT, "NOT"))
            else:
                tokens.append(Token(TokenType.TERM, word))

            i = j

        return tokens

    def parse(self, tokens: list[Token]) -> ASTNode:
        """Parse tokens into an AST using recursive descent.

        Grammar:
            expr     -> and_expr (OR and_expr)*
            and_expr -> not_expr (AND not_expr)*
            not_expr -> NOT not_expr | primary
            primary  -> TERM | PHRASE | LPAREN expr RPAREN
        """
        self._tokens = tokens
        self._pos = 0

        if not tokens:
            raise ParseError("Empty query")

        node = self._parse_or()

        if self._pos < len(self._tokens):
            raise ParseError(
                f"Unexpected token: {self._tokens[self._pos].value}"
            )

        return node

    def _peek(self) -> Token | None:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self) -> Token:
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        while self._peek() and self._peek().type == TokenType.OR:
            self._advance()  # consume OR
            right = self._parse_and()
            left = OrNode(left, right)
        return left

    def _parse_and(self) -> ASTNode:
        left = self._parse_not()
        while self._peek() and self._peek().type == TokenType.AND:
            self._advance()  # consume AND
            right = self._parse_not()
            left = AndNode(left, right)
        return left

    def _parse_not(self) -> ASTNode:
        if self._peek() and self._peek().type == TokenType.NOT:
            self._advance()  # consume NOT
            child = self._parse_not()  # NOT is right-associative
            return NotNode(child)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        token = self._peek()
        if token is None:
            raise ParseError("Unexpected end of query")

        if token.type == TokenType.TERM:
            self._advance()
            return TermNode(token.value)

        if token.type == TokenType.PHRASE:
            self._advance()
            return PhraseNode(token.phrase if hasattr(token, 'phrase') else token.value)

        if token.type == TokenType.LPAREN:
            self._advance()  # consume (
            node = self._parse_or()
            if not self._peek() or self._peek().type != TokenType.RPAREN:
                raise ParseError("Missing closing parenthesis")
            self._advance()  # consume )
            return node

        raise ParseError(f"Unexpected token: {token.value}")

    def evaluate(self, node: ASTNode, text: str,
                 case_sensitive: bool = False) -> list[tuple[int, int]]:
        """Evaluate AST against text. Returns match spans for highlighting.

        For AND: returns spans from both sides if both match.
        For OR: returns spans from whichever side(s) match.
        For NOT: returns empty list (NOT nodes filter; they don't highlight).
        """
        search_text = text if case_sensitive else text.lower()

        if isinstance(node, TermNode):
            term = node.term if case_sensitive else node.term.lower()
            return self._find_all(search_text, term, text)

        if isinstance(node, PhraseNode):
            phrase = node.phrase if case_sensitive else node.phrase.lower()
            return self._find_all(search_text, phrase, text)

        if isinstance(node, AndNode):
            left_spans = self.evaluate(node.left, text, case_sensitive)
            right_spans = self.evaluate(node.right, text, case_sensitive)
            # Both sides must have matches
            left_matches = self._has_positive_matches(node.left, left_spans, text, case_sensitive)
            right_matches = self._has_positive_matches(node.right, right_spans, text, case_sensitive)
            if left_matches and right_matches:
                return left_spans + right_spans
            return []

        if isinstance(node, OrNode):
            left_spans = self.evaluate(node.left, text, case_sensitive)
            right_spans = self.evaluate(node.right, text, case_sensitive)
            return left_spans + right_spans

        if isinstance(node, NotNode):
            child_spans = self.evaluate(node.child, text, case_sensitive)
            # NOT matches if child has NO matches
            if child_spans:
                return []  # Signal: NOT condition failed
            return [(-1, -1)]  # Signal: NOT condition passed (no highlight)

        return []

    def _has_positive_matches(self, node: ASTNode, spans: list[tuple[int, int]],
                               text: str, case_sensitive: bool) -> bool:
        """Check if a node actually matched (handles NOT nodes specially)."""
        if isinstance(node, NotNode):
            # NOT node "matches" when child has zero spans
            child_spans = self.evaluate(node.child, text, case_sensitive)
            return len(child_spans) == 0
        return len(spans) > 0

    def _find_all(self, search_text: str, query: str,
                  original_text: str) -> list[tuple[int, int]]:
        """Find all occurrences of query in text, return spans in original text."""
        spans = []
        start = 0
        while True:
            idx = search_text.find(query, start)
            if idx == -1:
                break
            spans.append((idx, idx + len(query)))
            start = idx + 1
        return spans

    def find_matches(self, text: str, query: str,
                     case_sensitive: bool = False) -> list[tuple[int, int]]:
        """High-level: parse query and find all match spans in text."""
        tokens = self.tokenize(query)
        if not tokens:
            return []

        try:
            ast = self.parse(tokens)
        except ParseError:
            # Fall back to plain text search if parsing fails
            lower_text = text if case_sensitive else text.lower()
            lower_query = query if case_sensitive else query.lower()
            spans = []
            start = 0
            while True:
                idx = lower_text.find(lower_query, start)
                if idx == -1:
                    break
                spans.append((idx, idx + len(lower_query)))
                start = idx + 1
            return spans

        spans = self.evaluate(ast, text, case_sensitive)
        # Filter out sentinel values from NOT nodes
        return [(s, e) for s, e in spans if s >= 0]
