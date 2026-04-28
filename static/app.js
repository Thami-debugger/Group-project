const PIECES = {
    K: "♔",
    Q: "♕",
    R: "♖",
    B: "♗",
    N: "♘",
    P: "♙",
    k: "♚",
    q: "♛",
    r: "♜",
    b: "♝",
    n: "♞",
    p: "♟",
};

const SAMPLE_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
const SAMPLE_CAPTURE_FEN = "k1n1n3/p2p1p2/P2P1P2/8/8/8/8/7K b - - 23 30";
const SAMPLE_SENSING_FENS = [
    "1k6/1ppn4/8/8/8/1P1P4/PN3P2/2K5 w - - 0 32",
    "1k6/1ppnP3/8/8/8/1P1P4/PN3P2/2K5 w - - 0 32",
    "1k6/1ppn1p2/8/8/8/1P1P4/PN3P2/2K5 w - - 0 32",
];
const SAMPLE_SENSING_WINDOW = "c8:?;d8:?;e8:?;c7:p;d7:n;e7:?;c6:?;d6:?;e6:?";

const boardGrid = document.getElementById("board-grid");
const boardMeta = document.getElementById("board-meta");
const fenPreview = document.getElementById("fen-preview");
const asciiPreview = document.getElementById("ascii-preview");
const healthStatus = document.getElementById("health-status");
const stockfishStatus = document.getElementById("stockfish-status");
const movesResults = document.getElementById("moves-results");
const statesResults = document.getElementById("states-results");
const selectResults = document.getElementById("select-results");
const stateCardTemplate = document.getElementById("state-card-template");
const playStatus = document.getElementById("play-status");
const playMeta = document.getElementById("play-meta");
const moveHistory = document.getElementById("move-history");

const gameState = {
    active: false,
    board: null,
    engineEnabled: true,
    playerColor: "white",
    startFen: null,
    moveUcis: [],
    selectedSquare: null,
    legalMoves: [],
    highlightedTargets: new Set(),
    history: [],
    lastMove: null,
    busy: false,
};

function setDefaultValues() {
    document.getElementById("board-fen").value = SAMPLE_FEN;
    document.getElementById("move-fen").value = SAMPLE_FEN;
    document.getElementById("moves-fen").value = SAMPLE_FEN;
    document.getElementById("states-fen").value = SAMPLE_FEN;
    document.getElementById("captures-fen").value = SAMPLE_CAPTURE_FEN;
    document.getElementById("capture-square").value = "d6";
    document.getElementById("sensing-fens").value = SAMPLE_SENSING_FENS.join("\n");
    document.getElementById("sensing-window").value = SAMPLE_SENSING_WINDOW;
    document.getElementById("select-single-fen").value = SAMPLE_FEN;
    document.getElementById("select-multiple-fens").value = SAMPLE_SENSING_FENS.join("\n");
    document.getElementById("play-fen").value = SAMPLE_FEN;
}

function renderBoard(board) {
    boardGrid.innerHTML = "";
    board.rows.forEach((row) => {
        row.forEach((square) => {
            const cell = document.createElement("div");
            cell.className = `square ${square.dark ? "dark" : "light"}`;
            cell.dataset.square = square.name;

            if (gameState.active) {
                if (gameState.selectedSquare === square.name) {
                    cell.classList.add("selected", "origin");
                }
                if (gameState.highlightedTargets.has(square.name)) {
                    cell.classList.add("target");
                }
                if (gameState.lastMove) {
                    if (gameState.lastMove.from === square.name) cell.classList.add("last-from");
                    if (gameState.lastMove.to === square.name) cell.classList.add("last-to");
                }
            }

            const piece = document.createElement("span");
            piece.className = `square-piece ${square.pieceColor ? `${square.pieceColor}-piece` : ""}`;
            piece.textContent = square.piece ? PIECES[square.piece] : "";

            const label = document.createElement("span");
            label.className = "square-label";
            label.textContent = square.name;

            cell.append(piece, label);
            cell.addEventListener("click", () => onBoardSquareClick(square));
            boardGrid.appendChild(cell);
        });
    });

    boardMeta.innerHTML = [
        `Turn: ${board.turn}`,
        `Check: ${board.isCheck ? "yes" : "no"}`,
        `Game Over: ${board.isGameOver ? "yes" : "no"}`,
        `Halfmove: ${board.halfmoveClock}`,
        `Fullmove: ${board.fullmoveNumber}`,
    ]
        .map((value) => `<span class="meta-pill">${value}</span>`)
        .join("");

    fenPreview.value = board.fen;
    asciiPreview.value = board.ascii;
}

function renderPlayMeta() {
    if (!gameState.active || !gameState.board) {
        playMeta.innerHTML = "";
        moveHistory.innerHTML = "";
        return;
    }

    playMeta.innerHTML = [
        `Engine: ${gameState.engineEnabled ? "on" : "off"}`,
        `To move: ${gameState.board.turn}`,
        `Legal moves: ${gameState.legalMoves.length}`,
        `Result: ${gameState.board.result || "in progress"}`,
    ]
        .map((value) => `<span class="meta-pill">${value}</span>`)
        .join("");

    moveHistory.innerHTML = "";
    gameState.history.forEach((entry) => {
        const item = document.createElement("li");
        item.textContent = entry;
        moveHistory.appendChild(item);
    });
}

function setPlayStatus(message, tone = "warning") {
    playStatus.className = `message-banner ${tone}`;
    playStatus.textContent = message;
}

function clearSelection() {
    gameState.selectedSquare = null;
    gameState.highlightedTargets = new Set();
    if (gameState.board) {
        renderBoard(gameState.board);
    }
}

function setGameBoard(board, legalMoves = null) {
    gameState.board = board;
    gameState.legalMoves = legalMoves || [];
    renderBoard(board);
    renderPlayMeta();
}

function legalMovesFromSquare(squareName) {
    return gameState.legalMoves.filter((move) => move.from === squareName);
}

async function startPlayableGame() {
    gameState.busy = true;
    try {
        const startFen = document.getElementById("play-fen").value;
        const result = await requestJson("/api/new-game", { fen: startFen });
        gameState.active = true;
        gameState.engineEnabled = document.getElementById("engine-enabled").checked;
        gameState.playerColor = document.querySelector('input[name="player-color"]:checked').value;
        gameState.startFen = result.board.fen;
        gameState.moveUcis = [];
        gameState.history = [];
        gameState.selectedSquare = null;
        gameState.highlightedTargets = new Set();
        gameState.lastMove = null;
        document.getElementById("game-controls").style.display = "";
        setGameBoard(result.board, result.legalMoves.moves);
        if (gameState.engineEnabled && !result.engineAvailable) {
            setPlayStatus("Engine is unavailable, so play mode is running as local two-player.", "warning");
            gameState.engineEnabled = false;
            document.getElementById("engine-enabled").checked = false;
        } else if (gameState.engineEnabled && gameState.playerColor === "black") {
            setPlayStatus("Engine is playing White. Waiting for engine first move…", "warning");
            await triggerEngineMove("white");
        } else {
            const colorLabel = gameState.playerColor === "white" ? "white" : "black";
            setPlayStatus(`Game started. Click one of your ${colorLabel} pieces, then click a highlighted square.`, "success");
        }
    } catch (error) {
        setPlayStatus(error.message, "error");
    } finally {
        gameState.busy = false;
    }
}

async function triggerEngineMove(engineColorName) {
    gameState.busy = true;
    try {
        const result = await requestJson("/api/engine-move", {
            fen: gameState.board.fen,
            engineColor: engineColorName,
        });
        if (result.engineMove) {
            const colorLabel = engineColorName === "white" ? "White" : "Black";
            gameState.history.push(`${colorLabel} (engine): ${result.engineMove}`);
            gameState.lastMove = {
                from: result.engineMove.slice(0, 2),
                to: result.engineMove.slice(2, 4),
            };
            gameState.moveUcis.push(result.engineMove);
        }
        setGameBoard(result.board, result.legalMoves.moves);
        if (result.board.isGameOver) {
            setPlayStatus(`Game over: ${result.board.result}`, "success");
        } else {
            const yourColor = gameState.playerColor;
            setPlayStatus(`Engine played ${result.engineMove}. Your turn — click one of your ${yourColor} pieces.`, "success");
        }
    } catch (error) {
        setPlayStatus(error.message, "error");
    } finally {
        gameState.busy = false;
    }
}

async function selectSquare(squareName) {
    if (!gameState.board) {
        return;
    }
    const result = await requestJson("/api/legal-moves", { fen: gameState.board.fen, square: squareName });
    const moves = result.moves;
    if (!moves.length) {
        clearSelection();
        setPlayStatus(`No legal moves from ${squareName}.`, "warning");
        return;
    }
    gameState.selectedSquare = squareName;
    gameState.highlightedTargets = new Set(moves.map((move) => move.to));
    renderBoard(gameState.board);
    setPlayStatus(`Selected ${squareName}. Choose a highlighted destination square.`, "success");
}

async function playSelectedMove(targetSquare) {
    const selectedMove = legalMovesFromSquare(gameState.selectedSquare).find((move) => move.to === targetSquare);
    if (!selectedMove) {
        setPlayStatus("That square is not a legal destination for the selected piece.", "warning");
        return;
    }

    gameState.busy = true;
    try {
        const engineColorName = gameState.playerColor === "white" ? "black" : "white";
        const result = await requestJson("/api/play-turn", {
            fen: gameState.board.fen,
            move: selectedMove.uci,
            engineEnabled: gameState.engineEnabled,
            engineColor: engineColorName,
        });

        const playerLabel = gameState.playerColor === "white" ? "White" : "Black";
        gameState.history.push(`${playerLabel}: ${result.playerMove}`);
        gameState.moveUcis.push(result.playerMove);
        gameState.lastMove = { from: result.playerMove.slice(0, 2), to: result.playerMove.slice(2, 4) };
        if (result.engineMove) {
            const engineLabel = engineColorName === "white" ? "White (engine)" : "Black (engine)";
            gameState.history.push(`${engineLabel}: ${result.engineMove}`);
            gameState.moveUcis.push(result.engineMove);
            gameState.lastMove = { from: result.engineMove.slice(0, 2), to: result.engineMove.slice(2, 4) };
        }
        gameState.selectedSquare = null;
        gameState.highlightedTargets = new Set();
        setGameBoard(result.board, result.legalMoves.moves);

        if (result.board.isGameOver) {
            setPlayStatus(`Game over: ${result.board.result}`, "success");
        } else if (result.engineMove) {
            setPlayStatus(`You played ${result.playerMove}. Engine replied with ${result.engineMove}.`, "success");
        } else {
            setPlayStatus(`Move played: ${result.playerMove}.`, "success");
        }
    } catch (error) {
        setPlayStatus(error.message, "error");
    } finally {
        gameState.busy = false;
    }
}

async function onBoardSquareClick(square) {
    if (!gameState.active || !gameState.board || gameState.busy || gameState.board.isGameOver) {
        return;
    }

    const squareName = square.name;
    const piece = square.piece;

    if (gameState.selectedSquare && gameState.highlightedTargets.has(squareName)) {
        await playSelectedMove(squareName);
        return;
    }

    if (!piece) {
        clearSelection();
        return;
    }

    const engineColorName = gameState.playerColor === "white" ? "black" : "white";
    if (gameState.board.turn === engineColorName && gameState.engineEnabled) {
        setPlayStatus("Wait for the engine reply before selecting another move.", "warning");
        return;
    }

    const isPlayerPiece = gameState.playerColor === "white"
        ? piece === piece.toUpperCase()
        : piece === piece.toLowerCase();
    if (!isPlayerPiece) {
        setPlayStatus(`You control ${gameState.playerColor}. Select one of your pieces.`, "warning");
        return;
    }

    await selectSquare(squareName);
}

function renderMiniBoard(container, board) {
    container.innerHTML = "";
    board.rows.forEach((row) => {
        row.forEach((square) => {
            const cell = document.createElement("div");
            cell.className = `mini-square ${square.dark ? "dark" : "light"}`;
            cell.textContent = square.piece ? PIECES[square.piece] : "";
            container.appendChild(cell);
        });
    });
}

function setBanner(container, message, tone = "success") {
    container.className = `message-banner ${tone}`;
    container.textContent = message;
}

function setEmpty(container, message) {
    container.className = "empty-state";
    container.textContent = message;
}

async function requestJson(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Request failed.");
    }
    return data;
}

function stateCards(states, titlePrefix) {
    statesResults.innerHTML = "";
    statesResults.className = "state-gallery";

    if (!states.length) {
        setEmpty(statesResults, "No states matched this query.");
        return;
    }

    states.forEach((state, index) => {
        const fragment = stateCardTemplate.content.cloneNode(true);
        const button = fragment.querySelector(".state-card");
        const miniBoard = fragment.querySelector(".mini-board");
        const title = fragment.querySelector(".state-title");
        const fen = fragment.querySelector(".state-fen");

        title.textContent = `${titlePrefix} ${index + 1}`;
        fen.textContent = state.fen;
        renderMiniBoard(miniBoard, state);
        button.addEventListener("click", () => renderBoard(state));

        statesResults.appendChild(fragment);
    });
}

function parseFenLines(text) {
    return text
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
}

async function loadHealth() {
    try {
        const response = await fetch("/api/health");
        const data = await response.json();
        healthStatus.textContent = data.ok ? "API ready" : "API unavailable";
        stockfishStatus.textContent = data.stockfishAvailable
            ? `Found at ${data.stockfishPath}`
            : `Missing at ${data.stockfishPath}`;
    } catch (error) {
        healthStatus.textContent = "API unavailable";
        stockfishStatus.textContent = "Health check failed";
    }
}

document.getElementById("load-sample-board").addEventListener("click", async () => {
    const board = await requestJson("/api/board", { fen: SAMPLE_FEN });
    renderBoard(board);
});

document.getElementById("play-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await startPlayableGame();
});

document.getElementById("reset-game").addEventListener("click", async () => {
    await startPlayableGame();
});

document.getElementById("undo-move").addEventListener("click", async () => {
    if (!gameState.active || gameState.busy || !gameState.moveUcis.length) {
        setPlayStatus("Nothing to undo.", "warning");
        return;
    }
    gameState.busy = true;
    try {
        // Remove last full round: player move + optional engine reply
        const movesToDrop = gameState.engineEnabled ? 2 : 1;
        const remaining = gameState.moveUcis.slice(0, Math.max(0, gameState.moveUcis.length - movesToDrop));
        const result = await requestJson("/api/replay", { fen: gameState.startFen, moves: remaining });
        gameState.moveUcis = remaining;
        gameState.history = gameState.history.slice(0, Math.max(0, gameState.history.length - movesToDrop));
        gameState.selectedSquare = null;
        gameState.highlightedTargets = new Set();
        gameState.lastMove = remaining.length >= 1
            ? { from: remaining[remaining.length - 1].slice(0, 2), to: remaining[remaining.length - 1].slice(2, 4) }
            : null;
        setGameBoard(result.board, result.legalMoves.moves);
        setPlayStatus("Move undone. Continue playing.", "success");
    } catch (error) {
        setPlayStatus(error.message, "error");
    } finally {
        gameState.busy = false;
    }
});

document.getElementById("resign-game").addEventListener("click", () => {
    if (!gameState.active || gameState.busy) return;
    gameState.active = false;
    const winner = gameState.playerColor === "white" ? "Black wins" : "White wins";
    setPlayStatus(`You resigned. ${winner}.`, "warning");
    renderPlayMeta();
});

document.getElementById("use-position").addEventListener("click", () => {
    if (!gameState.board) return;
    document.getElementById("play-fen").value = gameState.board.fen;
    setPlayStatus("Current position loaded into Start Position. Click Start Game to play from here.", "success");
});

document.getElementById("board-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const board = await requestJson("/api/board", { fen: document.getElementById("board-fen").value });
        renderBoard(board);
        setBanner(movesResults, "Board rendered. Preview updated.");
    } catch (error) {
        setBanner(movesResults, error.message, "error");
    }
});

document.getElementById("move-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const board = await requestJson("/api/move", {
            fen: document.getElementById("move-fen").value,
            move: document.getElementById("move-uci").value,
        });
        renderBoard(board);
        document.getElementById("move-fen").value = board.fen;
        setBanner(selectResults, `Move applied. New position loaded from ${board.fen}.`);
    } catch (error) {
        setBanner(selectResults, error.message, "error");
    }
});

document.getElementById("moves-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const result = await requestJson("/api/moves", { fen: document.getElementById("moves-fen").value });
        movesResults.innerHTML = "";
        movesResults.className = "chip-list";
        result.moves.forEach((move) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "chip";
            button.textContent = move;
            button.addEventListener("click", () => {
                document.getElementById("move-uci").value = move;
                document.getElementById("move-fen").value = result.fen;
            });
            movesResults.appendChild(button);
        });
    } catch (error) {
        setBanner(movesResults, error.message, "error");
    }
});

document.getElementById("states-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const result = await requestJson("/api/states", { fen: document.getElementById("states-fen").value });
        stateCards(result.states, "State");
    } catch (error) {
        setBanner(statesResults, error.message, "error");
    }
});

document.getElementById("captures-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const result = await requestJson("/api/captures", {
            fen: document.getElementById("captures-fen").value,
            square: document.getElementById("capture-square").value,
        });
        stateCards(result.states, "Capture State");
    } catch (error) {
        setBanner(statesResults, error.message, "error");
    }
});

document.getElementById("sensing-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const result = await requestJson("/api/sensing", {
            fens: parseFenLines(document.getElementById("sensing-fens").value),
            window: document.getElementById("sensing-window").value,
        });
        stateCards(result.states, "Sensed State");
    } catch (error) {
        setBanner(statesResults, error.message, "error");
    }
});

document.getElementById("select-single-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const result = await requestJson("/api/select-move", {
            mode: "single",
            fen: document.getElementById("select-single-fen").value,
        });
        renderBoard(result.board);
        setBanner(selectResults, `Selected move: ${result.move}`);
    } catch (error) {
        setBanner(selectResults, error.message, "warning");
    }
});

document.getElementById("select-multiple-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const result = await requestJson("/api/select-move", {
            mode: "multiple",
            fens: parseFenLines(document.getElementById("select-multiple-fens").value),
        });
        const votes = Object.entries(result.votes)
            .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
            .map(([move, count]) => `${move}: ${count}`)
            .join(" | ");
        setBanner(selectResults, `Majority vote move: ${result.move}. Votes: ${votes}`);
    } catch (error) {
        setBanner(selectResults, error.message, "warning");
    }
});

async function boot() {
    setDefaultValues();
    await loadHealth();
    const board = await requestJson("/api/board", { fen: SAMPLE_FEN });
    renderBoard(board);
    renderPlayMeta();
}

boot().catch((error) => {
    setBanner(selectResults, error.message, "error");
});