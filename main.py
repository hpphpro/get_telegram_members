from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.channels import GetFullChannelRequest
import pandas as pd 
from tqdm.asyncio import tqdm_asyncio

import asyncio
import re
import os
from getpass import getpass

from config import API_HASH, API_ID, source_path


client = TelegramClient('.anon', api_id=API_ID, api_hash=API_HASH) 




async def collect_all_members(group: str, limit: int, _step: int = 500) -> None:
    """

    Args:
        group (str): a name of the group
        limit (int): limit to parse
        _step (int): a step value that is substracts from limit

    Raises:
        TypeError/ValueError: if limit lower or equal zero or it instance is not an integer

    Returns:
        _type_: None
        
    Holding an error: 'ChannelParticipants' object is not subscriptable
    """
    
    if limit <= 0:
        raise ValueError(f'Cannot parse data with negative or zero limit, {limit=}')
    if not isinstance(limit, int):
        raise TypeError(f'Expected int value, got {type(limit).__name__}')
    try:
       
        members = await client.get_participants(group, aggressive=False, limit=limit)
        
        for member in tqdm_asyncio(members, desc=f'Collecting from {group}', total=len(members)):
            
            data = {
                'member_id': member.id,
                'username': member.username if member.username else '',
                'first_name': member.first_name if member.first_name else '',
                'last_name': member.last_name if member.last_name else '',
                'phone': member.phone if member.phone else '',
                'access_hash': member.access_hash,
                'is_bot': 'Not a bot' if not member.bot else "It's a bot"
            }

            path_to_save = source_path / 'members.csv'
            df = pd.DataFrame(data, index=[1])
            if os.path.exists(path_to_save):
                df.to_csv(path_to_save, index=False, mode='a', encoding='utf-8', header=False)
            else:
                df.to_csv(path_to_save, index=False, mode='w', encoding='utf-8')
                    
    except TypeError as ex:
        print(f'Got an error {ex}... retrying')
        return await collect_all_members(group=group, limit=(limit - _step))
    else:
        csv = pd.read_csv(path_to_save, encoding='utf-8')
        csv.drop_duplicates(inplace=True, ignore_index=True)
        csv.to_csv(path_to_save, encoding='utf-8', index=False)

    
            
async def get_member(limit: int | None = None) -> None:
    """
    Args:
        limit (int | None, optional): limit to parse. Defaults to None.
    If :param: limit is None it will take value of channel by default
    
    """
   
    await client.connect()
    
    if not await client.is_user_authorized():
        phone = input('Enter your phone: ')
        await client.send_code_request(phone)
        code = getpass('Enter code: ')
        await client.sign_in(phone, code)
    
    path_with_data = source_path / 'group_list.csv'
    if not os.path.exists(path_with_data):
        raise FileNotFoundError('A file with groups is required')
    
    csv = pd.read_csv(path_with_data, encoding='utf-8').to_string(index=False)
    groups_name = [group.split('/')[-1] for group in csv.split()] # getting only name from url
   
   
    for group in groups_name:
        
        try:
            await client(JoinChannelRequest(group))
            group_entity = await client.get_entity(group)
            group_data = await client(GetFullChannelRequest(channel=group_entity))

            match_list = re.findall(r"(?<='participants_count':)[\d ]+(?=,)", str(group_data.to_dict()), flags=re.IGNORECASE)
            members_value = max([int(number.strip()) for number in match_list if number.strip().isnumeric()])
            
            if not limit:
                limit = members_value
                
            await collect_all_members(group=group, limit=limit)
            
        except Exception as ex:
            print(f'Unexpected issue {ex}\nGroup:{group}')
            continue
        
        
async def main():
    await get_member()
    


if __name__ == '__main__':
    asyncio.run(main())
