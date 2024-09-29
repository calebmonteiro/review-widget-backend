import os
from groq import Groq
from scraper import fetch_product_info
import json

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
model = "llama3-70b-8192"
max_tries = 3

def get_product_and_description_from_url(url):
    title, description = fetch_product_info(url)

    num_tries = 0
    while(num_tries <= max_tries):
        pre_json_title_and_description = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert in e-commerce, writing titles and descriptions for products with ease. 
                    """
                },
                {
                    "role": "user",
                    "content": f"""Extract title, description, and category of the product from the HTML at this product page 
                    {title} and {description}. Make sure the description accurately describes the product. 
                    Return a title and description and category as a json object with no other output.
                    Make sure your output has those fields."""
                }
            ],
            model=model,
        )
        
        try:
            json_obj = json.loads(pre_json_title_and_description.choices[0].message.content)
            break
        except (TypeError, ValueError) as e:
            if (num_tries == 3):
                #(pre_json_title_and_description.choices[0].message.content)
                raise Exception("Invalid JSON object") from e
            else:
                num_tries+=1
                continue

    json_obj["url"] = url

    return json_obj


def get_questions_for_product(json_obj):
    num_tries = 0

    while(num_tries <= max_tries):
        pre_json_questions = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """You are an expert reviewer for e-commerce items, as well as how best to ask questions for other people to write as authentic and good reviews as you can. 
                """
            },
            {
                "role": "user",
                "content": f"""Generate short and easy questions to ask a user of {json_obj["title"]}. 
                Make sure the questions take into account the product's features, use cases, and categories
                like durability, affordibility, versatitlity, and accessibility from {json_obj["description"]}.
                Return only a JSON object of id and text field for each question, with no other output.
                Format like q#:text for each question. Just a series of q#:text"""
            }
        ],
        model=model,
        )

        try:
            json_questions = json.loads(pre_json_questions.choices[0].message.content)
            break
        except (TypeError, ValueError) as e:
            if (num_tries == 3):
                raise Exception("Invalid JSON object") from e
            else:
                num_tries+=1
                continue
    json_obj["questions"] = json_questions
    return json_obj

def generate_example_review(item, sentiment_category):
    example_review = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": f"""You are an expert in NLP and sentiment analysis, as well as writing reviews 
            showcasing specific categories like the product's {sentiment_category}. 
            """
        },
        {
            "role": "user",
            "content": f"""Generate a 2-4 line review of {item} that will be used to compare against other
            reviewer's in the category of {sentiment_category}
            Make sure the review take into account the {item}'s features, use cases, and categories
            and both perspectives on the item's {sentiment_category} (e.g. positive and negative)"""
        }
    ],
    model=model,
    )
    return example_review

if __name__ == "__main__":
    urls= [
        "https://kith.com/collections/kith-footwear/products/x2j162xf85500",
        "https://www.amazon.com/eos-Cashmere-Moisture-Lightweight-Non-Greasy/dp/B08KT2Z93D/?_encoding=UTF8&pd_rd_w=a3wu2&content-id=amzn1.sym.aeef70de-9e3e-4007-ae27-5dbb7b4a72f6&pf_rd_p=aeef70de-9e3e-4007-ae27-5dbb7b4a72f6&pf_rd_r=21NA7K6QEXX5X2F6N2KM&pd_rd_wg=l7cK3&pd_rd_r=903996a9-0eaa-4382-bfac-680c67cfe909&ref_=pd_hp_d_btf_crs_zg_bs_3760911",
        #Captcha"https://www.walmart.com/ip/Austin-Peanut-Butter-on-Cheese-Sandwich-Crackers-Single-Serve-Snack-Crackers-20-Count/1837462801?classType=REGULAR&athbdg=L1600&adsRedirect=true",
        #Timeout"https://www.meijer.com/shopping/product/sony-zx-series-stereo-headphones-black/2724286708.html",
        "https://us.shein.com/SHEIN-EZwear-Women-s-Hooded-Sweatshirt-With-Slogan-Print-And-Kangaroo-Pocket-FAITH-OVER-FEAR-PSALM-563-p-29621449.html?src_identifier=uf=usbingsearch09_cheaptrendyclothes02_20220804&src_module=ads&mallCode=1&pageListType=4&imgRatio=3-4",
        "https://www.gap.com/browse/product.do?pid=538469002&rrec=true&mlink=5001,1,home_gaphome2_rr_0&clink=1",
        "https://www.target.com/p/marvel-youth-spider-man-halloween-costume/-/A-90605950?preselect=90599841#lnk=sametab",
        "https://www.nike.com/t/ja-2-basketball-shoes-zNhj0Q/FD7328-500"
    ]
    for url in urls:
        prod_entry = get_product_and_description_from_url(url)
        final_entry = get_questions_for_product(prod_entry)
        print(final_entry)