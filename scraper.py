import requests
from bs4 import BeautifulSoup

base_url = "https://www.singaporepools.com.sg/en/product/sr/Pages/toto_results.aspx"
response = requests.get(base_url)
user_numbers = [8, 16, 17, 34, 38, 48]
if response.status_code == 200: #valid response
    #print(response.text)
    html_content = response.content
    soup = BeautifulSoup(html_content, 'html.parser')

    #draw date
    draw_date = soup.find(class_="drawDate").get_text(strip=True)
    print(draw_date)

    #winning numbers
    winning_numbers = soup.find_all(class_=lambda x: x and x.startswith("win"))
    winning_numbers = [int(num.get_text(strip=True)) for num in winning_numbers]
    print(winning_numbers)

    #additional number
    additional_number = int(soup.find(class_="additional").get_text(strip=True))
    print(additional_number)

    #group 1 prize
    group1_prize = soup.find(class_="jackpotPrize").get_text(strip=True)
    print(group1_prize)

    #prize money retrival
    prize_table = soup.find("table", class_="tableWinningShares")
    prize_rows = prize_table.find("tbody").find_all("tr")[1:] #skip header row
    prize_dict = {}
    for row in prize_rows:
        cols = row.find_all("td")
        prize_group = cols[0].get_text(strip=True)
        prize_amount = cols[1].get_text(strip=True)
        #no_of_winners = cols[2].get_text(strip=True)
        prize_dict[prize_group] = prize_amount
        print(prize_group, prize_amount)

    #calculate number of wins
    winning_count = 0
    for num in user_numbers:
        if num in winning_numbers:
            winning_count += 1
    print(winning_count)

    won_additional_number = additional_number in user_numbers
    if winning_count == 6:
        result_group = "Group 1"
    elif winning_count == 5 and won_additional_number:
        result_group = "Group 2"
    elif winning_count == 5:
        result_group = "Group 3"
    elif winning_count == 4 and won_additional_number:
        result_group = "Group 4"
    elif winning_count == 4:
        result_group = "Group 5"
    elif winning_count == 3 and won_additional_number:
        result_group = "Group 6"
    elif winning_count == 3:
        result_group = "Group 7"

    #display prize money
    if result_group:
        prize_amount = prize_dict.get(result_group, "Unknown")
        print(f"You won {result_group}")
        print(f"Your prize money is {prize_amount}")
    else:
        print("No prize")

else:
    print("Invalid response")
