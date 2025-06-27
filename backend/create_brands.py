#!/usr/bin/env python3
"""
Script to create brands in ChatCPG v2 - MVP version with GE Beauty
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import sessionmaker
from app.db.database import engine
from app.models.brand import Brand

# Create a synchronous session for the script
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def read_file_safely(file_path: Path) -> str:
    """Read file content safely, returning empty string if file doesn't exist"""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
    return ""


def create_ge_beauty_brand():
    """Create GE Beauty brand with comprehensive data"""
    
    # Path to gebeauty brand data
    gebeauty_path = Path("../chat_cpg/z_brands/gebeauty")
    
    # Read brand data files
    products_content = read_file_safely(gebeauty_path / "products.md")
    style_content = read_file_safely(gebeauty_path / "style.md")
    format_content = read_file_safely(gebeauty_path / "format_recommendations.md")
    
    # MVP: Create comprehensive brand data
    brand_data = {
        "name": "GE Beauty",
        "slug": "gebeauty", 
        "website_url": "https://gebeauty.com.br",
        "blog_url": "https://gebeauty.com.br/blogs/gebeauty",
        "brand_description": """GE Beauty é uma marca que nasceu para transformar a forma como lidamos com o cuidado capilar. 
Inspirada na diversidade brasileira, a linha é 100% vegana, clean beauty, testada dermatologicamente e focada em resultados reais.

A proposta é simples e inovadora: um sistema de cuidado capilar personalizável, baseado na combinação de bases + boosters + primers.""",
        "benchmarks": ["Gisou", "The Crown Affair", "Glossier", "Ouai", "Olaplex"],
        "style_guide": style_content if style_content else """Estilo moderno, clean e natural com foco na saúde capilar. 
Linguagem acessível e inclusiva, sempre valorizando a diversidade brasileira.""",
        "products_info": products_content if products_content else """Sistema personalizável de cuidado capilar com:
- Bases: Shampoo sem sulfato, Máscara condicionadora, Leave-in, Shampoo a seco
- Boosters: Antioxidante, Fortificante, Hidratante, Definição, Antifrizz  
- Primers: Cachos definidos, Lisos intactos""",
        "format_recommendations": format_content if format_content else """Posts de blog otimizados para SEO com estrutura:
- Títulos H1/H2 bem definidos
- Introdução engajante
- Conteúdo educativo sobre cuidados capilares
- CTAs naturais para produtos""",
        "knowledge_base": """Especialização em cuidados capilares para cabelos brasileiros diversos.
Foco em ingredientes naturais, sustentabilidade e resultados reais.
Clean beauty sem comprometer a performance."""
    }
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if brand already exists
        existing_brand = db.query(Brand).filter(Brand.slug == "gebeauty").first()
        
        if existing_brand:
            print("✏️  GE Beauty brand already exists. Updating...")
            
            # Update existing brand
            for key, value in brand_data.items():
                if hasattr(existing_brand, key):
                    setattr(existing_brand, key, value)
            
            db.commit()
            db.refresh(existing_brand)
            
            print(f"✅ Updated GE Beauty brand: {existing_brand.id}")
            brand = existing_brand
            
        else:
            print("🆕 Creating new GE Beauty brand...")
            
            # Create new brand
            new_brand = Brand(**brand_data)
            db.add(new_brand)
            db.commit()
            db.refresh(new_brand)
            
            print(f"✅ Created GE Beauty brand: {new_brand.id}")
            brand = new_brand
        
        # Display brand info
        print(f"""
📋 Brand Details:
   🏷️  Name: {brand.name}
   🔗 Slug: {brand.slug}
   🌐 Website: {brand.website_url}
   📝 Blog: {brand.blog_url}
   🎯 Benchmarks: {', '.join(brand.benchmarks or [])}
   📊 Data Status:
      - Style Guide: {'✅' if brand.style_guide else '❌'} ({len(brand.style_guide or '')} chars)
      - Products Info: {'✅' if brand.products_info else '❌'} ({len(brand.products_info or '')} chars)
      - Format Recs: {'✅' if brand.format_recommendations else '❌'} ({len(brand.format_recommendations or '')} chars)
      - Knowledge Base: {'✅' if brand.knowledge_base else '❌'} ({len(brand.knowledge_base or '')} chars)
        """)
        
        return brand
        
    except Exception as e:
        print(f"❌ Error creating/updating brand: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main function to create brands for MVP"""
    print("🚀 Setting up ChatCPG v2 MVP brands...")
    print("   Target: GE Beauty with comprehensive data")
    
    try:
        brand = create_ge_beauty_brand()
        print(f"\n✅ MVP brand setup completed successfully!")
        print(f"   Brand ID: {brand.id}")
        print(f"   Ready for chat with @{brand.slug}")
        
    except Exception as e:
        print(f"\n❌ Error setting up brands: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 