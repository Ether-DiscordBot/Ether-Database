import asyncio
import os
from typing import Optional
from beanie import init_beanie

from motor.motor_asyncio import AsyncIOMotorClient
from .models import (Guild, GuildUser, Logs, JoinLog, LeaveLog, ModerationLog, User, Playlist, ReactionRole, ReactionRoleOption)
try:
    from ether.core.utils import LevelsHandler
    levels_handler_import = True
except ImportError:
    levels_handler_import = False


class Database:

    client = None


    class Guild:
        async def create(guild_id: int):
            guild = Guild(id=guild_id)
            
            await guild.insert()
            
            return await Database.Guild.get_or_none(guild_id)
            
        async def get_or_create(guild_id: int):
            guild = await Database.Guild.get_or_none(guild_id)
            if guild:
                return guild
            
            return await Database.Guild.create(guild_id)
        
        async def get_or_none(guild_id: int):
            guild = await Guild.find_one(Guild.id == guild_id)
            if guild:
                return guild
            
            return None
        
        class Logs:
            class Moderation:
                async def set(guild_id: int, enabled: bool, channel_id: Optional[int] = None):
                    guild = await Database.Guild.get_or_none(guild_id)
                    
                    if not guild:
                        return None
                    
                    if channel_id:
                        moderation_logs = ModerationLog(channel_id=channel_id, enabled=enabled)
                    else:
                        if not (guild.logs and guild.logs.moderation):
                            return None
                        moderation_logs = ModerationLog(channel_id=guild.logs.moderation.channel_id, enabled=enabled)
                    
                    if guild.logs:
                        await guild.set({Guild.logs.moderation: moderation_logs})
                    else:
                        await guild.set({Guild.logs: Logs(moderation=moderation_logs)})
                        
                    return True
                    
                    
                    
    
    class GuildUser:
        async def create(user_id: int, guild_id: int):
            user = GuildUser(id=user_id, guild_id=guild_id)
            
            await user.insert()
            
            return await Database.GuildUser.get_or_none(user_id, guild_id)
            
        async def get_or_create(user_id: int, guild_id: int):
            user = await Database.GuildUser.get_or_none(user_id, guild_id)
            if user:
                return user
            
            return await Database.GuildUser.create(user_id, guild_id)
        
        async def get_or_none(user_id: int, guild_id: int):
            user = await GuildUser.find_one(GuildUser.id == user_id and GuildUser.guild_id == guild_id)
            if user:
                return user
            
            return None

        async def add_exp(user_id, guild_id, amount):
            if not levels_handler_import: return
            
            user = await Database.GuildUser.get_or_none(user_id, guild_id)
            
            if not user:
                return
            
            new_exp = user.exp + amount
            next_level = LevelsHandler.get_next_level(user.levels)
            if next_level <= new_exp:
                await user.set({GuildUser.exp: new_exp - next_level, GuildUser.levels: user.levels + 1})
                return user.levels
            
            await user.set({GuildUser.exp: new_exp})
        

async def init_database():
    Database.client = AsyncIOMotorClient(os.environ["MONGO_DB_URI"]).dbot
    
    await init_beanie(
        database=Database.client, document_models=[Guild, GuildUser, User]
    )
    
    _database = Database


loop = asyncio.get_event_loop()
loop.create_task(init_database())