CREATE_CATEGORY_OF_4_TYPES = """
                                For every "index:content", classify every "content" based on whether it contains an idea for improvement or not:
                                if there's no idea for improvement
                                    - value: 무의견 (if there is absolutely no information)
                                    - value: 만족 (if one is simply thankful for the service)
                                    - value: 불만족 (if one is simply dissatisfied with the service)
                                if there's an idea for improvement
                                    - value: 의견
                            """

FORMAT_CREATE_CATEGORY_OF_4_TYPES = """
                                    Input format is [index:content]
                                    Your output format MUST follow [index:value]
                                    Your number of outputs should be equal to the number of inputs
                                    (NEVER concatenate multiple indices into one line, eg. 41-44, 43~64 <- prohibited)
                                    """

EVAL_CATEGORY_OF_4_TYPES = """
                            For every "index:content:category", evaluate whether the category is accurate or not
                            1. Read content and think whether the category is accurate or not
                            2. If category is accurate, write a blank and skip
                            3. If category is not accurate, write a different category it should belong
                            4. If category is 의견, write your concise summary of the content (in Korean)
                                (Your summary should be concise/consistent enough to fit in a single line)
                            """

FORMAT_EVAL_CATEGORY_OF_4_TYPES = """
                                    Input format is [index:content:category]
                                    Your output format MUST follow [index:eval]
                                    Your number of outputs should be equal to the number of inputs
                                    (NEVER concatenate multiple indices into one line, eg. 41-44, 43~64 <- prohibited)
                                """

SUMMARIZE_OPINION = """
                        For every "index:suggestion:category",
                        write your concise summary of each suggestion (in Korean)
                        (Your summary should be concise/consistent enough to fit in a single line)
                    """

FORMAT_SUMMARIZE_OPINION = """
                            Input format is [index:suggestion:category]
                            Your output format MUST follow [index:summary]
                            Your number of outputs should be equal to the number of inputs
                            (NEVER concatenate multiple indices into one line, eg. 41-44, 43~64 <- prohibited)
                        """

SUMMARIZE_EVAL = """
                    For every "index:suggestion",
                    write two keywords that summarizes a main point of the suggestion (in Korean, no more than two words)
                """

FORMAT_SUMMARIZE_EVAL = """
                            Input format is [index:suggestion]
                            Your output format MUST follow [index:keyword]
                            Your number of outputs should be equal to the number of inputs
                        """

EVALUATE_AS_OTHERS = """
                    For every "index:opinion:opinion_category",
                    if opinion_category is 'blank', fill the blank with a category that fits the opinion
                    (The format should be similar to other opinion categories)
                    """

FORMAT_EVALUATE_AS_OTHERS = """
                            Input format is [index:opinion:opinion_category]
                            Your output format MUST follow [index:opinion_category]
                            """

ALL_MESSAGES = {
    
    'create category (of 4 types)': (CREATE_CATEGORY_OF_4_TYPES, FORMAT_CREATE_CATEGORY_OF_4_TYPES),
    'evaluate category': (EVAL_CATEGORY_OF_4_TYPES, FORMAT_EVAL_CATEGORY_OF_4_TYPES),
    'summarize opinion': (SUMMARIZE_OPINION, FORMAT_SUMMARIZE_OPINION),
    'summarize eval': (SUMMARIZE_EVAL, FORMAT_SUMMARIZE_EVAL),
    'evaluate as others': (EVALUATE_AS_OTHERS, FORMAT_EVALUATE_AS_OTHERS)

}