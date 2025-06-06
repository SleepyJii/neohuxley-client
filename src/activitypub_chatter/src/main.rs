use std::io;
use std::sync::{Arc, Mutex};

use serde_json::Value;
use clap::Parser;
use futures::{SinkExt, StreamExt};
use tokio::{sync::mpsc, task};
use tokio_tungstenite::connect_async;
use tui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    style::{Style},
    text::{Span, Spans},
    widgets::{Block, Borders, Paragraph},
    Terminal,
};
use url::Url;

use crossterm::{
    event::{self, Event as CEvent, KeyCode, KeyModifiers},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};

/// Simple TUI WebSocket client
#[derive(Parser, Debug)]
#[command(name = "chatter")]
struct Args {
    /// Host domain for ActivityPub server
    #[arg(long)]
    host: String,

    /// Target user@domain to chat with
    #[arg(long)]
    target: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();

    let ws_url = format!("ws://{}/chatter?target={}", args.host, args.target);
    let url = Url::parse(&ws_url)?;
    let (ws_stream, _) = connect_async(url).await?;
    let (mut write, mut read) = ws_stream.split();

    // Channels for communication between WebSocket task and UI
    let (tx_ui, mut rx_ui) = mpsc::unbounded_channel::<String>();
    let (tx_ws, mut rx_ws) = mpsc::unbounded_channel::<String>();

    // Spawn task: read from WebSocket, forward to UI
    task::spawn(async move {
        while let Some(Ok(msg)) = read.next().await {
            if let Ok(text) = msg.to_text() {
                // Parse as JSON and format
                if let Ok(json) = serde_json::from_str::<Value>(text) {
                    if let (Some(user), Some(content)) = (
                        json.get("user").and_then(|v| v.as_str()),
                        json.get("content").and_then(|v| v.as_str())
                    ) {
                        let _ = tx_ui.send(format!("{}: {}", user, content));
                    }
                }
            }
        }
    });

    // Spawn task: receive from input, send to WebSocket
    task::spawn(async move {
        while let Some(msg) = rx_ws.recv().await {
            let _ = write.send(msg.into()).await;
        }
    });

    // Terminal UI setup
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let messages = Arc::new(Mutex::new(Vec::new()));
    let scroll_offset = Arc::new(Mutex::new(0));
    let input = Arc::new(Mutex::new(String::new()));

    loop {
        // Draw UI
        terminal.draw(|f| {
            let size = f.size();
            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .margin(1)
                .constraints([Constraint::Min(1), Constraint::Length(3)].as_ref())
                .split(size);

            let msgs = messages.lock().unwrap();
            let text: Vec<Spans> = msgs.iter().map(|m| Spans::from(Span::raw(m))).collect();
            let messages_len = msgs.len();
            let height = chunks[0].height.saturating_sub(2) as usize;
            let offset = messages_len.saturating_sub(height);
            *scroll_offset.lock().unwrap() = offset;
            let messages_widget = Paragraph::new(text)
                .block(Block::default().borders(Borders::ALL).title("Messages"))
                .scroll((offset as u16, 0)); // vertical scroll

            let input_buf = input.lock().unwrap().clone();
            let input_widget = Paragraph::new(input_buf)
                .style(Style::default())
                .block(Block::default().borders(Borders::ALL).title("Input"));

            f.render_widget(messages_widget, chunks[0]);
            f.render_widget(input_widget, chunks[1]);
        })?;

        // Handle events
        if event::poll(std::time::Duration::from_millis(100))? {
            if let CEvent::Key(key) = event::read()? {
                match (key.code, key.modifiers) {
                    (KeyCode::Char('c'), KeyModifiers::CONTROL) => {break;}
                    (KeyCode::Esc, _) => {break;}
                    (KeyCode::Char(c), _) => {
                        input.lock().unwrap().push(c);
                    }
                    (KeyCode::Backspace, _) => {
                        input.lock().unwrap().pop();
                    }
                    (KeyCode::Enter, _) => {
                        let mut input_buf = input.lock().unwrap();
                        let msg = input_buf.trim().to_string();
                        if !msg.is_empty() {
                            tx_ws.send(msg.clone()).ok();
                            //messages.lock().unwrap().push(format!("You: {}", msg));
                        }
                        input_buf.clear();
                    }
                    _ => {}
                }
            }
        }

        // Check for new incoming messages from WebSocket
        while let Ok(msg) = rx_ui.try_recv() {
            messages.lock().unwrap().push(format!("> {}", msg));
        }
    }

    // Cleanup
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;
    Ok(())
}

