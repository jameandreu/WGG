from rich.console import Console
import logging
from enum import Enum
from typing import Optional, Callable
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align
from rich import box
import pandas as pd
import time
from datetime import date
from rich.columns import Columns
import pyperclip
from io import StringIO

console = Console()
output = StringIO()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('menu_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MenuChoice(Enum):
    """Enum for menu choices to ensure type safety"""
    GENERATE_WEEKLY_GOALS = 1
    COMPARE = 2
    END_OF_WEEK_SUMMARY = 3
    QUIT = 4
    
class workWeek(Enum):
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6

class difficulty(Enum):
    EASY = 2
    NORMAL = 3
    HARD = 8

def print_summary(df):
    easy = 0
    normal = 0
    hard = 0
    total = 0    
    
    raw = {
        difficulty.EASY: ('EASY', df[df['Level of Difficulty (Dev)'] == 'EASY']),
        difficulty.NORMAL: ('NORMAL', df[df['Level of Difficulty (Dev)'] == 'NORMAL']),
        difficulty.HARD: ('HARD', df[df['Level of Difficulty (Dev)'] == 'HARD'])
    }
    
    for level_enum, (level_name, level_df) in raw.items():
        count = len(level_df)
        if level_name == "EASY":
            easy += count
        elif level_name == "NORMAL":
            normal += count
        elif level_name == "HARD":
            hard += count
        total += count
    print() 
    print(f"SUMMARY:")   
    print(f"EASY: {easy}")
    print(f"NORMAL: {normal}")
    print(f"HARD: {hard}")
    print(f"Grand Total: {total}")
    
def read_csv_file(file_path):

    encodings = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            print(f"Trying encoding: {encoding}")
            df = pd.read_csv(file_path, encoding=encoding)
            console.print(f"[green]Successfully read with encoding: {encoding}[/green]")
            break
        except UnicodeDecodeError:
            continue
    else:
        # If none of the encodings work, try with error handling
        try:
            df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
            console.print(f"[green]Read with UTF-8 and ignored errors[/green]")
        except Exception as e:
            console.print(f"[red]Failed to read file with any encoding:[/red] : {e}")
            # print(f"Failed to read file with any encoding: {e}")
            return None
    
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        
        # Display basic information about the dataset
        console.print(f"[green]Successfully loaded CSV file: {file_path}[/green]")
        console.print(f"[white on magenta]Shape: {df.shape} (rows, columns)[/white on magenta]")
        columns = list(df.columns)
        colors = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]
        styled_columns = [
            f"[{colors[i % len(colors)]}]{col}[/]" for i, col in enumerate(columns)
        ]
        console.print(Columns(styled_columns))
        print()
        # print("\nFirst 5 rows:")
        # print(df.head())
        
        return df
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{file_path}' is empty.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    
def print_output(raw_data):
    easy = 0
    normal = 0
    hard = 0
    total = 0   
    today = date.today()
    iso_year, iso_week, _ = today.isocalendar()

    # Calculate Monday of the ISO week
    monday = date.fromisocalendar(iso_year, iso_week, 1)  # 1 = Monday

    # Calculate Friday of the ISO week
    friday = date.fromisocalendar(iso_year, iso_week, 5)  # 5 = Friday 
    
    month_name = monday.strftime("%B")
    
    output.write("*WEEKLY GOALS*\n")
    output.write(f"Ubag, Andrew - JWD - {month_name} {monday.day}-{friday.day}, {iso_year}\n")
    output.write("\n")
    for day_enum, (day_name, day_df) in raw_data.items():
        # if day_name not in ("SATURDAY", "SUNDAY"):
        output.write(f"*{day_name}*\n")
        
        if not {'Project', 'Issue'}.issubset(day_df.columns):
            output.write("_N/A_\n\n")
            continue
        
        # Drop rows with missing 'Project' or 'Issue' (optional, for cleaner output)
        day_df = day_df.dropna(subset=['Project', 'Issue'])
        
        if day_df.empty:
            output.write("_N/A_\n\n")
            continue

        # Group by 'Project'
        for project, group in day_df.groupby('Project'):
            output.write(f"_*{project}*_\n")
            for _, row in group.iterrows():
                issue = row['Issue']
                difficulty = row['Level of Difficulty (Dev)']
                if difficulty == "EASY":
                 easy += 1
                elif difficulty == "NORMAL":
                    normal += 1
                elif difficulty == "HARD":
                    hard += 1
                total += 1

                output.write(f"• {issue} - {difficulty}\n")
            output.write("\n")
          # newline for readability
        
        


        
    output.write(f"SUMMARY:\n")   
    output.write(f"EASY: {easy}\n")
    output.write(f"NORMAL: {normal}\n")
    output.write(f"HARD: {hard}\n")
    output.write(f"Grand Total: {total}\n")
    
    formatted_output = output.getvalue()
    output.close()
    pyperclip.copy(formatted_output)
    console.print(formatted_output)
    console.print("[green]Output successfully copied to clipboard 📋📋📋[/green]")
    
def extract_data_from_this_week(df):
    today = date.today()
    current_week = today.isocalendar().week
    # current_week = 29
    current_year = today.isocalendar().year

    if 'Week' in df.columns:
        tasks_this_week = df[df['Week'] == current_week].drop_duplicates(subset=['Issue'])
    elif 'Due date' in df.columns:
        # Ensure 'Due date' is datetime
        df['Due date'] = pd.to_datetime(df['Due date'], errors='coerce')
        df['Week'] = df['Due date'].dt.isocalendar().week
        df['Year'] = df['Due date'].dt.isocalendar().year
        # print("COLUMNS!!!" + df.columns)
        tasks_this_week = df[(df['Week'] == current_week) & (df['Year'] == current_year)].drop_duplicates(subset=['#'])
    else:
        # If neither column exists, return empty DataFrame or raise an error
        tasks_this_week = pd.DataFrame(columns=df.columns)

    return tasks_this_week    
def process_data(tasks_this_week):
    
    reference_date = 'Date'
    if 'Due date' in tasks_this_week.columns:
        reference_date = 'Due date'



    
    if 'Issue' not in tasks_this_week.columns:
        required_issue_cols = {'Tracker', '#', 'Subject'}
        if required_issue_cols.issubset(tasks_this_week.columns):
            tasks_this_week['Issue'] = (
                tasks_this_week['Tracker'].fillna('').astype(str) +
                ' #' +
                tasks_this_week['#'].fillna('').astype(str) +
                ': ' +
                tasks_this_week['Subject'].fillna('').astype(str)
            )
        else:
            tasks_this_week['Issue'] = pd.NA 
        # print('test')
        
    tasks_this_week[reference_date] = pd.to_datetime(tasks_this_week[reference_date], errors='coerce')
    tasks_this_week['Day'] = tasks_this_week[reference_date].dt.day_name()
    


    # print("Rows before date conversion:", len(tasks_this_week))
    # print("Parsed reference date:", tasks_this_week[reference_date].head())
    # print("Day column:", tasks_this_week['Day'].unique())
    # print("Tracker values:", tasks_this_week['Tracker'].unique())
    # Filter out rows where 'tracker' is 'deployment'
    filtered = tasks_this_week[(tasks_this_week['Tracker'].str.lower() != 'deployment') & (tasks_this_week['Status'].str.lower() != 'deploy request')]

    days = [
        (workWeek.MONDAY, 'Monday'),
        (workWeek.TUESDAY, 'Tuesday'),
        (workWeek.WEDNESDAY, 'Wednesday'),
        (workWeek.THURSDAY, 'Thursday'),
        (workWeek.FRIDAY, 'Friday'),
    ]

    raw = {
        key: (name.upper(), filtered[filtered['Day'] == name])
        for key, name in days
    }
    
    # print(filtered['Issue'])
    
    return raw


def merge_raws(raw1, raw2):
    merged = {}
    seen_ids = set()
    
    
    ordered_keys = [
        workWeek.MONDAY,
        workWeek.TUESDAY,
        workWeek.WEDNESDAY,
        workWeek.THURSDAY,
        workWeek.FRIDAY,
    ]

    for key in ordered_keys:
        name = raw1[key][0]
        df1 = raw1[key][1]
        df2 = raw2[key][1]

        # combined_df = pd.concat([df1, df2], ignore_index=True).drop_duplicates()
        frames = [df for df in [df1, df2] if not df.empty]
        combined_df = pd.concat(frames, ignore_index=True).drop_duplicates() if frames else pd.DataFrame()
        
        if not combined_df.empty:
            combined_df = combined_df[~combined_df['Issue'].isin(seen_ids)]
            seen_ids.update(combined_df['Issue'])


        merged[key] = (name, combined_df)

    return merged
    
def generate_weekly_goals():
    """Handle weekly goals generation"""
    logger.info("User selected: Generate Weekly Goals")
    
    # Create a beautiful panel for the task
    panel = Panel(
        "[bold green]📊 Weekly Goals Generator[/bold green]\n\n"
        "Please put your redmine CSV to [bold cyan]redmines folder[/bold cyan]...\n"
        "[yellow]⚠️  Make sure to check [bold][u]ALL COLUMNS AND CHOOSE ENCODING: UTF-8[/u][/bold] when exporting tickets[/yellow]",
        
        title="[bold blue]Task Instructions[/bold blue]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)
    
    # Simulate processing with a progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Processing CSV files...", total=None)
        df = read_csv_file('redmine/timelog.csv')
        time.sleep(1)  
        progress.update(task, description="Generating weekly goals...")
        tasks_this_week = extract_data_from_this_week(df)
        raw = process_data(tasks_this_week)
        
        
        time.sleep(1)
        print_output(raw)
        # print_summary(tasks_this_week)
    
    # Success message
    success_panel = Panel(
        "[bold green]✅ Weekly goals generation completed successfully![/bold green]",
        title="[bold green]Success[/bold green]",
        border_style="green",
        padding=(0, 2)
    )
    console.print(success_panel)
def eow_feature():
    # logger.info("User selected: Compare feature")
    
    # # Create a warning panel for unimplemented feature
    # panel = Panel(
    #     "[bold yellow]🚧 Feature Under Development[/bold yellow]\n\n"
    #     "This feature is not implemented yet...\n"
    #     "[dim]This will be available in a future update.[/dim]",
    #     title="[bold yellow]EOW Summary Feature[/bold yellow]",
    #     border_style="yellow",
    #     padding=(1, 2)
    # )
    # console.print(panel)
    
    
    """Handle weekly goals generation"""
    logger.info("User selected: End of Week Summary")
    
    # Create a beautiful panel for the task
    panel = Panel(
        "[bold green]📈 End of Week Summary[/bold green]\n\n"
        "Please put your redmine CSV to [bold cyan]redmines folder[/bold cyan]...\n"
        "[yellow]⚠️  Make sure to check [bold][u]ALL COLUMNS AND CHOOSE ENCODING: UTF-8[/u][/bold] when exporting tickets[/yellow]",
        
        title="[bold blue]Task Instructions[/bold blue]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)
    
    # Simulate processing with a progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Processing CSV files...", total=None)
        df = read_csv_file('redmine/timelog.csv')
        time.sleep(1)  
        progress.update(task, description="Generating weekly goals...")
        tasks_this_week = extract_data_from_this_week(df)
        # raw = process_data(tasks_this_week)
        
        
        time.sleep(1)
        # print_output(raw)
        print_summary(tasks_this_week)
def compare_feature():
    """Handle compare feature"""
    # logger.info("User selected: Compare feature")
    
    # # Create a warning panel for unimplemented feature
    # panel = Panel(
    #     "[bold yellow]🚧 Feature Under Development[/bold yellow]\n\n"
    #     "This feature is not implemented yet...\n"
    #     "[dim]This will be available in a future update.[/dim]",
    #     title="[bold yellow]Compare Feature[/bold yellow]",
    #     border_style="yellow",
    #     padding=(1, 2)
    # )
    # console.print(panel)
    
    
    logger.info("User selected: Merge feature")
    
    
    panel = Panel(
        "[bold green]📊 Merge[/bold green]\n\n"
        "Please put your redmine CSV to [bold cyan]redmine folder[/bold cyan]...\n"
        
        "[yellow]⚠️  Make sure to check [bold][u]ALL COLUMNS AND CHOOSE ENCODING: UTF-8[/u][/bold] when exporting tickets[/yellow]",
        
        title="[bold blue]Task Instructions[/bold blue]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)
    
    # Simulate processing with a progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Processing CSV files...", total=None)
        df = read_csv_file('redmine/timelog.csv')
        time.sleep(1)  
        progress.update(task, description="Generating weekly goals...")
        tasks_this_week = extract_data_from_this_week(df)
        raw1 = process_data(tasks_this_week)
        
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Processing CSV files...", total=None)
        df = read_csv_file('redmine/issues.csv')
        time.sleep(1)  
        progress.update(task, description="Generating weekly goals...")
        tasks_this_week = extract_data_from_this_week(df)
        raw2 = process_data(tasks_this_week)
        
        
        time.sleep(1)
        raw = merge_raws(raw1, raw2)
        print_output(raw)

def quit_application():
    """Handle application exit"""
    logger.info("User chose to quit application")
    
    # Create a goodbye panel
    goodbye_panel = Panel(
        "[bold cyan]👋 Thank you for using the application![/bold cyan]\n\n"
        "[dim]Have a great day![/dim]",
        title="[bold cyan]Goodbye[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(goodbye_panel)
    return False  # Signal to stop the main loop

def display_menu():
    """Display a beautiful menu using Rich components"""
    # Create a table for the menu
    table = Table(
        title="[bold magenta]🎯 MAIN MENU[/bold magenta]",
        show_header=True,
        header_style="bold blue",
        border_style="bright_blue",
        box=box.ROUNDED
    )
    
    table.add_column("Option", style="bold cyan", justify="center", width=8)
    table.add_column("Description", style="white", width=25)
    table.add_column("Status", style="green", justify="center", width=12)
    
    # Add menu items
    table.add_row("1", "📊 Generate Weekly Goals", "✅ Ready")
    table.add_row("2", "🔍 Compare", "✅ Ready")
    table.add_row("3", "📈 End of Week Summary", "🚧 Coming Soon")
    table.add_row("4", "🚪 Quit", "✅ Ready")
    
    # Create a panel around the table
    menu_panel = Panel(
        Align.center(table),
        title="[bold green]Welcome to Goal Manager[/bold green]",
        subtitle="[dim]Select an option to continue[/dim]",
        border_style="green",
        padding=(1, 2)
    )
    
    console.print(menu_panel)

def get_user_choice() -> Optional[Callable]:
    """Get and validate user input with improved error handling"""
    menu_options = {
        MenuChoice.GENERATE_WEEKLY_GOALS: ("Generate Weekly Goals", generate_weekly_goals),
        MenuChoice.COMPARE: ("Compare", compare_feature),
        MenuChoice.END_OF_WEEK_SUMMARY: ("EOW", eow_feature),
        MenuChoice.QUIT: ("Quit", quit_application)
    }
    
    while True:
        try:
            # Display the beautiful menu
            display_menu()
            
            # Get user input with Rich prompt
            choice_value = IntPrompt.ask(
                "[bold cyan]Enter your choice[/bold cyan]",
                choices=["1", "2", "3", "4"],
                show_choices=True,
                show_default=False
            )
            
            # Convert to enum for type safety
            try:
                choice_enum = MenuChoice(choice_value)
            except ValueError:
                console.print("[red]❌ Invalid choice! Please try again.[/red]")
                logger.warning(f"Invalid menu choice attempted: {choice_value}")
                continue
            
            logger.info(f"Valid menu choice selected: {choice_enum.name}")
            return menu_options[choice_enum][1]  # Return the function
                
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Operation cancelled by user. Goodbye![/yellow]")
            logger.info("Application interrupted by user (Ctrl+C)")
            return quit_application
            
        except Exception as e:
            error_panel = Panel(
                f"[red]❌ An unexpected error occurred: {str(e)}[/red]",
                title="[bold red]Error[/bold red]",
                border_style="red"
            )
            console.print(error_panel)
            logger.error(f"Unexpected error in get_user_choice: {str(e)}")

def main():
    """Main application loop"""
    logger.info("Application started")
    
    # Display welcome banner
    welcome_text = Text("🎯 GOAL MANAGER", style="bold magenta")
    welcome_panel = Panel(
        Align.center(welcome_text),
        title="[bold green]Welcome[/bold green]",
        subtitle="[dim]Your productivity companion[/dim]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(welcome_panel)
    
    try:
        while True:
            selected_function = get_user_choice()
            
            if selected_function:
                try:
                    # Execute the selected function
                    result = selected_function()
                    
                    # If the function returns False, exit the loop (quit option)
                    if result is False:
                        break
                    
                    # Ask if user wants to continue with a beautiful prompt
                    console.print()
                    continue_choice = Prompt.ask(
                        "[bold cyan]Press Enter to return to main menu, or 'q' to quit[/bold cyan]",
                        choices=["", "q"],
                        show_choices=False,
                        default=""
                    )
                    
                    if continue_choice.lower() == 'q':
                        quit_application()
                        break
                        
                except Exception as e:
                    error_panel = Panel(
                        f"[red]❌ Error executing function: {str(e)}[/red]\n\n"
                        "[yellow]📋 Returning to main menu...[/yellow]",
                        title="[bold red]Error[/bold red]",
                        border_style="red",
                        padding=(1, 2)
                    )
                    console.print(error_panel)
                    logger.error(f"Error executing selected function: {str(e)}")
            else:
                logger.warning("No function selected, returning to menu")
                
    except Exception as e:
        fatal_panel = Panel(
            f"[red]💀 Fatal error: {str(e)}[/red]",
            title="[bold red]Fatal Error[/bold red]",
            border_style="red",
            padding=(1, 2)
        )
        console.print(fatal_panel)
        logger.critical(f"Fatal error in main loop: {str(e)}")
    
    finally:
        logger.info("Application shutting down")
        console.print("[dim]Application closed.[/dim]")

if __name__ == "__main__":
    main()