"""Postfix (RPN) expression evaluator — compilers/algorithms classic."""


def eval_postfix(tokens: list[str]) -> int:
    stack: list[int] = []
    for token in tokens:
        if token in {"+", "-", "*", "/"}:
            right = stack.pop()
            left = stack.pop()
            if token == "+":
                stack.append(left + right)
            elif token == "-":
                stack.append(left - right)
            elif token == "*":
                stack.append(left * right)
            else:
                stack.append(left // right)
        else:
            stack.append(int(token))
    return stack[-1]
